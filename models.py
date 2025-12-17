"""Database models for the GymSphere application."""
from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Application user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    age = db.Column(db.Integer)
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    target_weight_kg = db.Column(db.Float)

    body_level = db.Column(db.String(50))
    activity_level = db.Column(db.String(50))
    fitness_level = db.Column(db.String(50))
    freq_per_week = db.Column(db.Integer)
    goal = db.Column(db.String(100))
    estimate_days = db.Column(db.Integer)
    last_check_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Streak Tracking
    workout_streak = db.Column(db.Integer, default=0)
    diet_streak = db.Column(db.Integer, default=0)
    last_workout_date = db.Column(db.Date)
    last_diet_date = db.Column(db.Date)

    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    progress_logs = db.relationship(
        "UserProgress",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    orders = db.relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"





class DietPlan(db.Model):
    """Diet plan definition."""

    __tablename__ = "diet_plans"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fats = db.Column(db.Float)
    goal = db.Column(db.String(100))
    description = db.Column(db.Text)

    def __repr__(self) -> str:
        return f"<DietPlan {self.name}>"


class Product(db.Model):
    """Store product/equipment."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Enhanced fields
    image_url = db.Column(db.String(500)) # High quality image
    equipment_type = db.Column(db.String(50)) # e.g., dumbbell, mat, band
    neon_border_color = db.Column(db.String(20)) # e.g., cyan-400
    
    # Shopping Engine fields
    affiliate_url = db.Column(db.String(500))
    rating = db.Column(db.Float, default=4.5)
    src = db.Column(db.String(50), default="local") # local, amazon, flipkart

    def __repr__(self) -> str:
        return f"<Product {self.name}>"


class Exercise(db.Model):
    """Store exercise details."""

    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    muscle_group = db.Column(db.String(50))
    difficulty = db.Column(db.String(20)) # Beginner, Intermediate, Advanced
    equipment = db.Column(db.String(100)) # Bodyweight, Dumbbells, etc.
    description = db.Column(db.Text)
    
    # Enhanced Visuals
    animation_type = db.Column(db.String(20)) # lottie, gif, video
    animation_url = db.Column(db.String(500)) # URL to asset
    thumbnail_url = db.Column(db.String(500)) # Static preview
    
    tags = db.Column(db.String(200)) # Comma-separated tags

    def __repr__(self) -> str:
        return f"<Exercise {self.name}>"


class WaterLog(db.Model):
    """Track daily water intake."""
    __tablename__ = "water_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    amount_ml = db.Column(db.Integer, default=0) # Total for the day
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SleepLog(db.Model):
    """Track nightly sleep."""
    __tablename__ = "sleep_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = db.Column(db.Date, default=datetime.utcnow, nullable=False) # The morning of waking up
    hours = db.Column(db.Float, default=0.0)
    quality = db.Column(db.String(20)) # Good, Average, Poor

class Badge(db.Model):
    """Gamification badges."""
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    icon = db.Column(db.String(50)) # Emoji or icon name
    description = db.Column(db.String(200))
    criteria_json = db.Column(db.JSON) # Logic for awarding

class UserBadge(db.Model):
    """Badges earned by users."""
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    badge_id = db.Column(db.Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    badge = db.relationship("Badge")
    user = db.relationship("User", backref="badges")


class UserProgress(db.Model):
    """Weight/progress log per user."""

    __tablename__ = "user_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    weight = db.Column(db.Float)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="progress_logs")

    def __repr__(self) -> str:
        return f"<UserProgress user={self.user_id} at {self.logged_at}>"


class Notification(db.Model):
    """User notification."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # New fields for Smart Notification Engine
    type = db.Column(db.String(50), default="info") # reminder, plan, system, shopping
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    payload_json = db.Column(db.JSON) # For extra data like links
    scheduled_for = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.title}>"


class Order(db.Model):
    """Store order."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order {self.id} user={self.user_id}>"


class UserPlan(db.Model):
    """User's 30-day workout and diet plan."""

    __tablename__ = "user_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_type = db.Column(db.String(50), default="workout+diet")
    goal = db.Column(db.String(100))
    preference = db.Column(db.String(50))  # veg, nonveg, mixed
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    frequency_per_week = db.Column(db.Integer)
    fitness_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    metadata_json = db.Column(db.JSON)  # For summary, break days list, etc.

    daily_entries = db.relationship(
        "DailyPlanEntry",
        back_populates="plan",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<UserPlan {self.id} user={self.user_id} start={self.start_date}>"


class DailyPlanEntry(db.Model):
    """Daily entry for a user plan."""

    __tablename__ = "daily_plan_entries"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, ForeignKey("user_plans.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    is_exercise_day = db.Column(db.Boolean, default=False)
    exercise_payload = db.Column(db.JSON)  # List of exercises
    diet_payload = db.Column(db.JSON)  # Macros, meals
    
    # Completion status
    is_exercise_completed = db.Column(db.Boolean, default=False)
    exercise_completed_at = db.Column(db.DateTime)
    
    is_diet_completed = db.Column(db.Boolean, default=False)
    diet_completed_at = db.Column(db.DateTime)

    streak_group = db.Column(db.Integer)  # Optimization for streak queries

    plan = db.relationship("UserPlan", back_populates="daily_entries")
    checkins = db.relationship(
        "UserCheckIn",
        back_populates="daily_entry",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        db.Index("idx_plan_date", "plan_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<DailyPlanEntry {self.date} plan={self.plan_id}>"


class UserCheckIn(db.Model):
    """Log of user check-ins."""

    __tablename__ = "user_checkins"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    daily_entry_id = db.Column(db.Integer, ForeignKey("daily_plan_entries.id"), nullable=False)
    type = db.Column(db.String(20))  # exercise, diet, both
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)

    daily_entry = db.relationship("DailyPlanEntry", back_populates="checkins")

    def __repr__(self) -> str:
        return f"<UserCheckIn {self.type} user={self.user_id}>"
