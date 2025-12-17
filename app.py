"""
GymSphere Flask Application

A production-ready fitness app with AI-powered workout and nutrition recommendations.

Quick Start:
1. Install dependencies: pip install -r requirements.txt
2. Initialize database: flask --app app initdb
3. Seed data: python seed_data.py
4. Create admin: flask --app app create-admin
5. Run: python run.py or flask --app app run

The app includes:
- User authentication (Flask-Login)
- Onboarding flow (goal, body type, measurements, activity, fitness level)
- AI recommendations (workouts, diet, meal plans)
- Progress tracking with charts
- Admin panel for managing exercises, diet plans, and products
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    flash,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import Notification, Order, Product, User, UserProgress, WaterLog, SleepLog, Badge, UserBadge, db
from utils import (
    estimate_transformation_days,
    generate_weekly_mealplan,
    recommend_diet,
    recommend_shopping,
    recommend_workout,
)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return User.query.get(int(user_id))

    @app.route("/intro")
    def intro():
        return render_template("intro.html")

    @app.route("/_status")
    def status():
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "GymSphere"})

    @app.route("/_health")
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy"})

    @app.route("/")
    def index():
        if not session.get("intro_shown"):
            session["intro_shown"] = True
            return redirect(url_for("intro"))
        return render_template("index.html")

    @app.route("/goal", methods=["GET", "POST"])
    def goal():
        if request.method == "POST" and current_user.is_authenticated:
            current_user.goal = request.form.get("goal")
            db.session.commit()
            return redirect(url_for("body_type"))
        return render_template("goal_select.html")

    @app.route("/body-type", methods=["GET", "POST"])
    def body_type():
        if request.method == "POST" and current_user.is_authenticated:
            current_user.body_level = request.form.get("body_type")
            db.session.commit()
            return redirect(url_for("measurements"))
        return render_template("body_type.html")

    @app.route("/measurements", methods=["GET", "POST"])
    def measurements():
        if request.method == "POST" and current_user.is_authenticated:
            current_user.height_cm = request.form.get("height_cm") or current_user.height_cm
            current_user.weight_kg = request.form.get("weight_kg") or current_user.weight_kg
            current_user.target_weight_kg = request.form.get("target_weight_kg") or current_user.target_weight_kg
            db.session.commit()
            return redirect(url_for("activity"))
        return render_template("measurements.html")

    @app.route("/activity", methods=["GET", "POST"])
    def activity():
        if request.method == "POST" and current_user.is_authenticated:
            current_user.activity_level = request.form.get("activity_level")
            current_user.freq_per_week = request.form.get("freq_per_week") or current_user.freq_per_week
            db.session.commit()
            return redirect(url_for("fitness_level"))
        return render_template("activity.html")

    @app.route("/fitness-level", methods=["GET", "POST"])
    def fitness_level():
        if request.method == "POST" and current_user.is_authenticated:
            current_user.fitness_level = request.form.get("fitness_level")
            db.session.commit()
            return redirect(url_for("dashboard"))
        return render_template("fitness_level.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form.get("email").strip().lower()
            if User.query.filter_by(email=email).first():
                flash("Email already registered", "warning")
                return redirect(url_for("register"))
            user = User(
                fullname=request.form.get("fullname"),
                email=email,
                password_hash=generate_password_hash(request.form.get("password")),
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("goal"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email").strip().lower()
            password = request.form.get("password")
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "danger")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.route("/api/onboard", methods=["POST"])
    @login_required
    def api_onboard():
        data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
        for field in [
            "goal",
            "body_level",
            "activity_level",
            "fitness_level",
        ]:
            if field in data:
                setattr(current_user, field, data[field])
        for field in ["height_cm", "weight_kg", "target_weight_kg", "freq_per_week"]:
            if field in data:
                setattr(current_user, field, data[field])
        db.session.commit()
        return jsonify({"status": "ok"})

    @app.route("/dashboard")
    @login_required
    def dashboard():
        # Hub Dashboard: Focus on Today + Summary
        workout = snippet = diet = None
        
        try:
            # 1. Today's Workout Snippet
            from utils import recommend_workout
            full_workout = recommend_workout(current_user.goal, current_user.fitness_level, current_user.freq_per_week or 3)
            
            workout = {
                "frequency": full_workout.get("frequency"),
                "exercises": full_workout.get("exercises", [])[:3], 
                "total_exercises": len(full_workout.get("exercises", [])),
                "duration_min": "45"
            }

            # 2. Today's Diet Target
            from utils import recommend_diet
            diet = recommend_diet(current_user.weight_kg, current_user.target_weight_kg, current_user.goal)
            
            # 3. Gamification & Streaks (Needed for Dashboard Summary)
            from utils import check_notifications_engine
            check_notifications_engine(current_user)
            
            workout_streak = current_user.workout_streak
            diet_streak = current_user.diet_streak
            
        except Exception as e:
            print(f"Dashboard Error: {e}")
            # Fallbacks
            if not workout:
                workout = {"frequency": 3, "exercises": [], "total_exercises": 0, "duration_min": 0}
            if not diet:
                diet = {"calories": 0, "macros": {"protein_g": 0, "carbs_g": 0, "fats_g": 0}} # Ensure accurate fallback structure
            workout_streak = current_user.workout_streak or 0
            diet_streak = current_user.diet_streak or 0

        return render_template(
            "dashboard.html",
            workout=workout,
            diet=diet,
            user=current_user,
            workout_streak=workout_streak,
            diet_streak=diet_streak
        )

    @app.route("/workout")
    @login_required
    def workout_page():
        from utils import recommend_workout, get_equipment_for_workout
        workout = recommend_workout(current_user.goal, current_user.fitness_level, current_user.freq_per_week or 3)
        equipment = get_equipment_for_workout(workout.get("exercises", []))
        return render_template("workout.html", workout=workout, equipment=equipment)

    @app.route("/shop")
    @login_required
    def shop_page():
        return render_template("shopping.html", user=current_user)

    @app.route("/diet")
    @login_required
    def diet_page():
        from utils import recommend_diet, generate_weekly_mealplan
        diet = recommend_diet(current_user.weight_kg, current_user.target_weight_kg, current_user.goal)
        mealplan = generate_weekly_mealplan(diet or {}, current_user.goal)
        return render_template("diet.html", diet=diet, mealplan=mealplan)

    @app.route("/progress")
    @login_required
    def progress_page():
        # Fetch detailed progress data
        progress_logs = (
            UserProgress.query.filter_by(user_id=current_user.id)
            .order_by(UserProgress.logged_at.asc())
            .all()
        )
        progress_labels = [log.logged_at.strftime("%Y-%m-%d") for log in progress_logs]
        progress_values = [log.weight for log in progress_logs]
        
        # 2. Lifestyle Data (Moved from Dashboard)
        today_date = datetime.utcnow().date()
        water_logs = WaterLog.query.filter(
            WaterLog.user_id == current_user.id,
            WaterLog.date == today_date
        ).all()
        hydration_current = sum(log.amount_ml for log in water_logs)
        hydration_goal = 3000 
        
        sleep_log = SleepLog.query.filter(
            SleepLog.user_id == current_user.id,
            SleepLog.date == today_date
        ).first()
        sleep_data = {"hours": sleep_log.hours if sleep_log else 0, "quality": sleep_log.quality if sleep_log else "-"}
        
        return render_template(
            "progress.html", 
            progress_labels=progress_labels, 
            progress_values=progress_values,
            hydration_data={"current": hydration_current, "goal": hydration_goal},
            sleep_data=sleep_data
        )

    @app.route("/account")
    @login_required
    def account_page():
        user_badges = [ub.badge for ub in current_user.badges]
        return render_template("account.html", user=current_user, badges=user_badges)

    @app.route("/update_progress", methods=["POST"])
    @login_required
    def update_progress():
        weight = request.form.get("weight")
        if weight:
            entry = UserProgress(user_id=current_user.id, weight=float(weight), logged_at=datetime.utcnow())
            db.session.add(entry)
            db.session.commit()
        return redirect(url_for("progress_page"))

    @app.route("/admin")
    @login_required
    def admin():
        if not current_user.is_admin:
            flash("Admin access required", "warning")
            return redirect(url_for("dashboard"))
        from models import DietPlan, Exercise
        exercises = Exercise.query.all()
        diet_plans = DietPlan.query.all()
        products = Product.query.all()
        return render_template(
            "admin.html",
            exercises=exercises,
            diet_plans=diet_plans,
            products=products,
        )



    # --- Plan API Endpoints ---

    @app.route("/api/plan/generate", methods=["POST"])
    @login_required
    def api_plan_generate():
        data = request.get_json(force=True, silent=True) or {}
        start_date = data.get("start_date")
        
        from utils import generate_month_plan
        plan = generate_month_plan(current_user, start_date)
        
        return jsonify({
            "status": "ok",
            "plan_id": plan.id,
            "message": "Plan generated successfully"
        })

    @app.route("/api/plan/today")
    @login_required
    def api_plan_today():
        from models import DailyPlanEntry, UserPlan
        
        today = datetime.utcnow().date()
        
        # Find active plan (end date >= today)
        plan = UserPlan.query.filter(
            UserPlan.user_id == current_user.id,
            UserPlan.end_date >= today
        ).order_by(UserPlan.created_at.desc()).first()
        
        if not plan:
            return jsonify({"status": "no_plan"})
            
        entry = DailyPlanEntry.query.filter_by(plan_id=plan.id, date=today).first()
        if not entry:
             return jsonify({"status": "no_entry_for_today"})
             
        return jsonify({
            "status": "ok",
            "entry": {
                "id": entry.id,
                "date": entry.date.isoformat(),
                "is_exercise_day": entry.is_exercise_day,
                "is_exercise_completed": entry.is_exercise_completed,
                "is_diet_completed": entry.is_diet_completed,
                "exercise_payload": entry.exercise_payload,
                "diet_payload": entry.diet_payload
            }
        })

    @app.route("/api/plan/checkin", methods=["POST"])
    @login_required
    def api_plan_checkin():
        from models import DailyPlanEntry, UserCheckIn, UserPlan
        from utils import schedule_next_day_notifications, compute_streaks
        
        data = request.get_json()
        entry_id = data.get("entry_id")
        checkin_type = data.get("type") # exercise, diet
        
        entry = DailyPlanEntry.query.get_or_404(entry_id)
        if entry.plan.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
            
        # Update status
        if checkin_type == "exercise":
            entry.is_exercise_completed = True
            entry.exercise_completed_at = datetime.utcnow()
        elif checkin_type == "diet":
            entry.is_diet_completed = True
            entry.diet_completed_at = datetime.utcnow()
            
        # Log check-in
        checkin = UserCheckIn(
            user_id=current_user.id,
            daily_entry_id=entry.id,
            type=checkin_type,
            note=data.get("note")
        )
        db.session.add(checkin)
        db.session.commit()
        
        # Trigger updates
        schedule_next_day_notifications(current_user, entry.plan_id)
        streaks = compute_streaks(current_user.id, entry.plan_id)
        
        return jsonify({
            "status": "ok",
            "streaks": streaks
        })

    @app.route("/api/plan/calendar")
    @login_required
    def api_plan_calendar():
        from models import DailyPlanEntry, UserPlan
        
        # Get active plan
        today = datetime.utcnow().date()
        plan = UserPlan.query.filter(
            UserPlan.user_id == current_user.id
        ).order_by(UserPlan.created_at.desc()).first()
        
        if not plan:
             return jsonify([])
             
        entries = DailyPlanEntry.query.filter_by(plan_id=plan.id).all()
        
        result = []
        for e in entries:
            # Determine status color/state for frontend
            status = "future"
            if e.date < today:
                if (e.is_exercise_day and e.is_exercise_completed and e.is_diet_completed) or \
                   (not e.is_exercise_day and e.is_diet_completed):
                    status = "completed"
                else:
                    status = "missed"
            elif e.date == today:
                 if (e.is_exercise_day and e.is_exercise_completed and e.is_diet_completed) or \
                   (not e.is_exercise_day and e.is_diet_completed):
                    status = "completed"
                 else:
                    status = "today"
            
            result.append({
                "date": e.date.isoformat(),
                "is_exercise_day": e.is_exercise_day,
                "is_exercise_completed": e.is_exercise_completed,
                "is_diet_completed": e.is_diet_completed,
                "status": status
            })
            
        return jsonify(result)

    @app.route("/api/plan/stats")
    @login_required
    def api_plan_stats():
        from models import UserPlan
        from utils import compute_streaks
        
        today = datetime.utcnow().date()
        plan = UserPlan.query.filter(
            UserPlan.user_id == current_user.id,
            UserPlan.end_date >= today
        ).order_by(UserPlan.created_at.desc()).first()
        
        if not plan:
            return jsonify({"current_streak": 0, "longest_streak": 0})
            
        streaks = compute_streaks(current_user.id, plan.id)
        return jsonify(streaks)

    # --- Feature APIs ---

    @app.route("/api/notifications")
    @login_required
    def api_notifications():
        from models import Notification
        
        # Unread first, then recent read
        notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
            Notification.is_read.asc(),
            Notification.created_at.desc()
        ).limit(20).all()
        
        return jsonify([{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
            "payload": n.payload_json
        } for n in notifs])

    @app.route("/api/notifications/read", methods=["POST"])
    @login_required
    def api_notifications_read():
        from models import Notification
        data = request.get_json(silent=True) or {}
        notif_id = data.get("id")
        
        if notif_id:
            n = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
            if n:
                n.is_read = True
                db.session.commit()
        else:
            # Mark all as read
            Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
            db.session.commit()
            
        return jsonify({"status": "ok"})

    @app.route("/api/shop/recommend")
    @login_required
    def api_shop_recommend():
        from utils import recommend_shopping
        
        items = recommend_shopping(current_user.goal, app)
        return jsonify(items)

    @app.route("/api/water/log", methods=["POST"])
    @login_required
    def api_water_log():
        data = request.get_json(silent=True) or {}
        amount = data.get("amount", 250)
        
        # Check if already logged today? Or just append?
        # Model allows multiple entries per day? 
        # Actually WaterLog seems to track each 'sip' or we can aggregate.
        # But 'date' field implies one entry per day if unique constraint exists.
        # models.py doesn't show unique constraint on date+user_id.
        # But if we just add new rows for same date, we sum them up.
        
        log = WaterLog(user_id=current_user.id, amount_ml=amount, date=datetime.utcnow().date())
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"status": "ok", "added": amount})

    @app.route("/api/sleep/log", methods=["POST"])
    @login_required
    def api_sleep_log():
        data = request.get_json(silent=True) or {}
        hours = data.get("hours", 8)
        quality = data.get("quality", "Good")
        
        log = SleepLog(user_id=current_user.id, hours=hours, quality=quality, date=datetime.utcnow().date())
        db.session.add(log)
        db.session.commit()
        return jsonify({"status": "ok"})

    @app.route("/api/leaderboard")
    @login_required
    def api_leaderboard():
        # Mock leaderboard for demo mostly, or real query
        # Top 5 users by "active days" (using UserProgress count as proxy)
        
        top_users = db.session.query(
            User.fullname, db.func.count(UserProgress.id).label('score')
        ).join(UserProgress).group_by(User.id).order_by(db.desc('score')).limit(5).all()
        
        leaderboard = [{"name": u.fullname, "score": u.score, "metric": "Check-ins"} for u in top_users]
        
        # Add Admin if empty (for demo)
        if not leaderboard:
            leaderboard = [{"name": "Admin User", "score": 42, "metric": "Workouts"}, {"name": "Bot One", "score": 30, "metric": "Workouts"}]
            
        return jsonify(leaderboard)


    @app.cli.command("initdb")
    def initdb_command():
        """Initialize the database."""
        with app.app_context():
            db.create_all()
        print("Database initialized.")

    @app.cli.command("create-admin")
    def create_admin_command():
        """Create an admin user via CLI prompts."""
        import getpass

        name = input("Full name: ")
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        with app.app_context():
            if User.query.filter_by(email=email).first():
                print("User already exists.")
                return
            admin = User(
                fullname=name,
                email=email,
                password_hash=generate_password_hash(password),
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin created.")

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
