"""Seed data for GymSphere."""
from datetime import datetime, timedelta

from flask import Flask
from werkzeug.security import generate_password_hash

from app import create_app
from models import DietPlan, Exercise, Product, User, UserProgress, Notification, db


def seed_exercises():
    """Seed a comprehensive library of exercises."""
    exercises = [
        # --- WARMUP / MOBILITY ---
        {"name": "Arm Circles", "tags": "warmup,mobility", "muscle_group": "Shoulders", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Leg Swings", "tags": "warmup,mobility", "muscle_group": "Legs", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Cat-Cow Stretch", "tags": "warmup,mobility,back", "muscle_group": "Back", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Jumping Jacks", "tags": "warmup,cardio", "muscle_group": "Full Body", "equipment": "Bodyweight", "difficulty": "Beginner"},
        
        # --- CHEST ---
        {"name": "Push-Ups", "tags": "chest,strength", "muscle_group": "Chest", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Dumbbell Bench Press", "tags": "chest,strength", "muscle_group": "Chest", "equipment": "Dumbbells, Bench", "difficulty": "Intermediate"},
        {"name": "Incline Dumbbell Press", "tags": "chest,strength", "muscle_group": "Chest", "equipment": "Dumbbells, Bench", "difficulty": "Intermediate"},
        {"name": "Chest Flyes", "tags": "chest,isolation", "muscle_group": "Chest", "equipment": "Dumbbells, Bench", "difficulty": "Intermediate"},
        
        # --- BACK ---
        {"name": "Pull-Ups", "tags": "back,strength", "muscle_group": "Back", "equipment": "Pull-up Bar", "difficulty": "Advanced"},
        {"name": "Dumbbell Rows", "tags": "back,strength", "muscle_group": "Back", "equipment": "Dumbbells, Bench", "difficulty": "Intermediate"},
        {"name": "Superman", "tags": "back,core", "muscle_group": "Back", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Lat Pulldown (Band)", "tags": "back,isolation", "muscle_group": "Back", "equipment": "Resistance Bands", "difficulty": "Beginner"},
        
        # --- LEGS ---
        {"name": "Bodyweight Squats", "tags": "legs,strength", "muscle_group": "Legs", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Goblet Squats", "tags": "legs,strength", "muscle_group": "Legs", "equipment": "Dumbbells", "difficulty": "Intermediate"},
        {"name": "Lunges", "tags": "legs,strength", "muscle_group": "Legs", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Romanian Deadlift", "tags": "legs,hamstrings", "muscle_group": "Legs", "equipment": "Dumbbells", "difficulty": "Intermediate"},
        {"name": "Calf Raises", "tags": "legs,isolation", "muscle_group": "Legs", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Glute Bridges", "tags": "legs,glutes", "muscle_group": "Legs", "equipment": "Bodyweight", "difficulty": "Beginner"},
        
        # --- SHOULDERS ---
        {"name": "Dumbbell Overhead Press", "tags": "shoulders,strength", "muscle_group": "Shoulders", "equipment": "Dumbbells", "difficulty": "Intermediate"},
        {"name": "Lateral Raises", "tags": "shoulders,isolation", "muscle_group": "Shoulders", "equipment": "Dumbbells", "difficulty": "Intermediate"},
        {"name": "Front Raises", "tags": "shoulders,isolation", "muscle_group": "Shoulders", "equipment": "Dumbbells", "difficulty": "Beginner"},
        
        # --- ARMS ---
        {"name": "Bicep Curls", "tags": "arms,biceps", "muscle_group": "Arms", "equipment": "Dumbbells", "difficulty": "Beginner"},
        {"name": "Hammer Curls", "tags": "arms,biceps", "muscle_group": "Arms", "equipment": "Dumbbells", "difficulty": "Beginner"},
        {"name": "Tricep Dips", "tags": "arms,triceps", "muscle_group": "Arms", "equipment": "Bench", "difficulty": "Intermediate"},
        {"name": "Overhead Tricep Ext", "tags": "arms,triceps", "muscle_group": "Arms", "equipment": "Dumbbells", "difficulty": "Intermediate"},
        
        # --- CORE / ABS ---
        {"name": "Plank", "tags": "abs,core,stability", "muscle_group": "Core", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Crunches", "tags": "abs,core", "muscle_group": "Core", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Russian Twists", "tags": "abs,core", "muscle_group": "Core", "equipment": "Bodyweight", "difficulty": "Intermediate"},
        {"name": "Leg Raises", "tags": "abs,core", "muscle_group": "Core", "equipment": "Bodyweight", "difficulty": "Intermediate"},
        {"name": "Bicycle Crunches", "tags": "abs,core", "muscle_group": "Core", "equipment": "Bodyweight", "difficulty": "Intermediate"},
        {"name": "Ab Wheel Rollout", "tags": "abs,advanced", "muscle_group": "Core", "equipment": "Ab Wheel", "difficulty": "Advanced"},
        
        # --- FINISHER / HIIT ---
        {"name": "Burpees", "tags": "hiit,finisher,cardio", "muscle_group": "Full Body", "equipment": "Bodyweight", "difficulty": "Advanced"},
        {"name": "Mountain Climbers", "tags": "hiit,finisher,core", "muscle_group": "Core", "equipment": "Bodyweight", "difficulty": "Intermediate"},
        {"name": "High Knees", "tags": "hiit,cardio", "muscle_group": "Legs", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Kettlebell Swings", "tags": "hiit,strength", "muscle_group": "Full Body", "equipment": "Kettlebell", "difficulty": "Intermediate"},
        
        # --- COOLDOWN / STRETCH ---
        {"name": "Child's Pose", "tags": "stretch,cooldown", "muscle_group": "Full Body", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Hamstring Stretch", "tags": "stretch,cooldown", "muscle_group": "Legs", "equipment": "Bodyweight", "difficulty": "Beginner"},
        {"name": "Chest Stretch", "tags": "stretch,cooldown", "muscle_group": "Chest", "equipment": "Bodyweight", "difficulty": "Beginner"},
    ]
    
    for ex in exercises:
        if not Exercise.query.filter_by(name=ex["name"]).first():
            new_ex = Exercise(
                name=ex["name"],
                muscle_group=ex["muscle_group"],
                difficulty=ex["difficulty"],
                equipment=ex["equipment"],
                description=f"Perform {ex['name']} with proper form.",
                tags=ex["tags"],
                animation_type="lottie",
                animation_url="https://assets.lottiefiles.com/packages/lf20_9xRkZk.json", # Placeholder
                thumbnail_url=f"https://placehold.co/400x300?text={ex['name'].replace(' ', '+')}"
            )
            db.session.add(new_ex)
    
    db.session.commit()
    print("[SUCCESS] Comprehensive exercise library seeded.")


def seed_diet_plans():
    plans = [
        {
            "name": "Weight Loss Plan",
            "calories": 1800,
            "protein": 140,
            "carbs": 170,
            "fats": 60,
            "goal": "lose",
            "description": "Moderate deficit with high protein.",
        },
        {
            "name": "Muscle Gain Plan",
            "calories": 2600,
            "protein": 170,
            "carbs": 300,
            "fats": 80,
            "goal": "gain",
            "description": "Slight surplus for lean muscle gain.",
        },
        {
            "name": "Recomposition Plan",
            "calories": 2200,
            "protein": 160,
            "carbs": 220,
            "fats": 70,
            "goal": "recomp",
            "description": "Maintenance calories with balanced macros.",
        },
    ]
    for plan in plans:
        if not DietPlan.query.filter_by(name=plan["name"]).first():
            db.session.add(DietPlan(**plan))


def seed_products():
    """Seed shopping and equipment."""
    # Clear existing if needed or just upsert
    
    products = [
        {"name": "Pro Series Resistance Bands", "price": 29.99, "category": "equipment", "equipment_type": "Resistance Bands", "description": "Heavy duty bands.", "image_url": "https://m.media-amazon.com/images/I/61wOdP9G+gL.jpg", "affiliate_url": "#"},
        {"name": "Smart Adjustable Dumbbells", "price": 199.99, "category": "equipment", "equipment_type": "Dumbbells", "description": "SelectTech weights.", "image_url": "https://m.media-amazon.com/images/I/71+pOdQ7iKL._AC_SX679_.jpg", "affiliate_url": "#"},
        {"name": "Premium Yoga Mat", "price": 45.00, "category": "equipment", "equipment_type": "Mat", "description": "Non-slip mat.", "image_url": "https://m.media-amazon.com/images/I/81+6iM6C5XL._AC_SX679_.jpg", "affiliate_url": "#"},
        {"name": "Gold Standard Whey", "price": 54.99, "category": "supplements", "equipment_type": "Supplement", "description": "Whey Isolate.", "image_url": "https://m.media-amazon.com/images/I/71+6P+H6+pL._AC_SX679_.jpg", "affiliate_url": "#"},
        {"name": "Ab Wheel Roller", "price": 19.99, "category": "equipment", "equipment_type": "Ab Wheel", "description": "Core strength tool.", "image_url": "https://m.media-amazon.com/images/I/71-Wl6+FmTL._AC_SX679_.jpg", "affiliate_url": "#"},
        {"name": "Kettlebell (16kg)", "price": 35.00, "category": "equipment", "equipment_type": "Kettlebell", "description": "Cast iron kettlebell.", "image_url": "https://m.media-amazon.com/images/I/61rLg3sZ+uL._AC_SX679_.jpg", "affiliate_url": "#"},
        {"name": "Pull-up Bar", "price": 25.00, "category": "equipment", "equipment_type": "Pull-up Bar", "description": "Doorway mount bar.", "image_url": "https://m.media-amazon.com/images/I/61-vA0mR-KL._AC_SX679_.jpg", "affiliate_url": "#"},
    ]
    
    for p in products:
        existing = Product.query.filter_by(name=p["name"]).first()
        if existing:
            # Update existing product
            existing.image_url = p["image_url"]
            # Update other fields just in case
            existing.price = p["price"]
            existing.description = p["description"]
            if p.get("affiliate_url"):
                existing.affiliate_url = p["affiliate_url"]
        else:
            new_p = Product(
                name=p["name"],
                price=p["price"],
                category=p["category"],
                equipment_type=p.get("equipment_type"),
                description=p["description"],
                image_url=p["image_url"],
                affiliate_url=p.get("affiliate_url"),
                rating=4.8,
                src="amazon"
            )
            db.session.add(new_p)
    db.session.commit()

def seed_badges():
    """Seed gamification badges."""
    from models import Badge
    badges = [
        {"name": "Newcomer", "icon": "🌱", "description": "Joined GymSphere.", "criteria_json": {"type": "join"}},
        {"name": "Streak Master", "icon": "🔥", "description": "Hit a 7-day streak.", "criteria_json": {"type": "streak", "value": 7}},
        {"name": "Early Bird", "icon": "🌅", "description": "Logged a workout before 8 AM.", "criteria_json": {"type": "time", "hour": 8}},
        {"name": "Heavy Lifter", "icon": "💪", "description": "Completed a muscle gain plan.", "criteria_json": {"type": "plan_complete", "goal": "muscle_gain"}},
        {"name": "Hydrated", "icon": "💧", "description": "Logged water intake for 3 days.", "criteria_json": {"type": "water_streak", "value": 3}},
    ]
    
    for b in badges:
        if not Badge.query.filter_by(name=b["name"]).first():
            db.session.add(Badge(
                name=b["name"],
                icon=b["icon"],
                description=b["description"],
                criteria_json=b["criteria_json"]
            ))
    db.session.commit()
    print("[SUCCESS] Badges seeded.")


def seed_admin_user():
    """Create admin user if not exists."""
    admin_email = "admin@example.com"
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            fullname="Admin User",
            email=admin_email,
            password_hash=generate_password_hash("admin123"),
            is_admin=True,
            created_at=datetime.utcnow(),
        )
        db.session.add(admin)
        db.session.flush()  # Get the admin ID
        
        # Add demo progress entries for admin
        base_date = datetime.utcnow() - timedelta(days=21)
        for i in range(3):
            progress = UserProgress(
                user_id=admin.id,
                weight=75.0 - (i * 0.5),  # Simulate weight loss
                logged_at=base_date + timedelta(days=i * 7),
            )
            db.session.add(progress)


def run_seed(app: Flask):
    """Seed all data in an idempotent way."""
    with app.app_context():
        db.create_all()
        seed_exercises()
        seed_diet_plans()
        seed_products()
        seed_badges()
        seed_admin_user()
        db.session.commit()
        print("[SUCCESS] Seed data created successfully!")


def seed_sample_plan(app):
    """Generate a sample plan for the admin user."""
    from utils import generate_month_plan
    from models import UserPlan
    
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        if admin and not UserPlan.query.filter_by(user_id=admin.id).first():
            print("Generating sample plan for admin...")
            generate_month_plan(admin)
            print("[SUCCESS] Sample plan generated.")



def seed_features(app):
    """Seed Shopping Products and Notifications."""
    print("Seeding Features (Products & Notifications)...")
    with app.app_context():
        # Products are seeded in seed_products()


        # Notifications for Admin
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            existing = Notification.query.filter_by(user_id=admin.id, type="system").first()
            if not existing:
                welcome = Notification(
                    user_id=admin.id,
                    title="Welcome to GymSphere 2.0 🚀",
                    message="Your dashboard has been upgraded! Check out the new Shopping section and your daily plan.",
                    type="system",
                    created_at=datetime.utcnow(),
                    is_read=False
                )
                db.session.add(welcome)
                print(" - Welcome notification seeded.")
        
        db.session.commit()
        print("[SUCCESS] Features seeded.")


if __name__ == "__main__":
    application = create_app()
    run_seed(application)
    seed_sample_plan(application)
    seed_features(application)
