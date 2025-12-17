from app import create_app
from models import db, User, Exercise, Product

app = create_app()
with app.app_context():
    try:
        user_count = User.query.count()
        exercise_count = Exercise.query.count()
        product_count = Product.query.count()
        print(f"Users: {user_count}")
        print(f"Exercises: {exercise_count}")
        print(f"Products: {product_count}")
    except Exception as e:
        print(f"Error accessing database: {e}")
