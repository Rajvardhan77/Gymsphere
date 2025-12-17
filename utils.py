"""Rule-based AI engine for GymSphere fitness recommendations."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models import Notification, Product, User, db


def estimate_transformation_days(weight: float, target: float, goal: str) -> int:
    """
    Estimate transformation days using linear regression-style calculation.
    
    Args:
        weight: Current weight in kg
        target: Target weight in kg
        goal: Goal type (fat_loss, muscle_gain, recomposition)
    
    Returns:
        Estimated days to reach target
    """
    if weight is None or target is None:
        return 0
    
    delta = target - weight
    kg_to_change = abs(delta)
    
    if kg_to_change < 0.1:
        return 0
    
    goal_lower = (goal or "").lower()
    
    # Rate ranges per week (kg/week)
    if goal_lower in ["fat_loss", "lose", "weight_loss"]:
        # Fat loss: 0.4-0.7 kg/week (use average 0.55)
        rate_per_week = 0.55
    elif goal_lower in ["muscle_gain", "gain", "bulk"]:
        # Muscle gain: 0.2-0.4 kg/week (use average 0.3)
        rate_per_week = 0.3
    elif goal_lower in ["recomposition", "recomp"]:
        # Recomposition: slower progression (0.15-0.25 kg/week, use 0.2)
        rate_per_week = 0.2
    else:
        # Default moderate rate
        rate_per_week = 0.4
    
    weeks_needed = kg_to_change / rate_per_week
    days = max(7, int(weeks_needed * 7))
    
    return days



def generate_exercises_list(goal: str, fitness_level: str, equipment: str) -> List[Dict]:
    """
    Generate a professional 10-15 exercise workout routine.
    Structure: Warm-up (2) -> Main (7-11) -> Finisher (1-2) -> Cool-down (1)
    """
    from models import Exercise  # Local import
    import random
    
    # Safety Check
    if not goal:
        goal = "general_fitness"
    
    # 1. Determine Difficulty & Targets
    diff_map = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}
    target_difficulty = diff_map.get(fitness_level, "Beginner")
    
    # Target Muscles based on Goal
    primary_muscles = []
    if "fat_loss" in goal: primary_muscles = ["Full Body", "Legs", "Chest", "Back"]
    elif "muscle_gain" in goal: primary_muscles = ["Chest", "Back", "Legs", "Shoulders", "Arms"]
    elif "core" in goal: primary_muscles = ["Abs", "Core", "Lower Back"]
    else: primary_muscles = ["Full Body"] # Default
    
    # Equipment Filter
    # If no_equipment, strictly bodyweight. If with_equipment, prefer equipment but allow bodyweight.
    require_equip = (equipment == "with_equipment")
    
    # Helper to fetch by tag/type
    def get_ex(tags, limit, allow_repeat=False, strict_muscle=False):
        query = Exercise.query
        
        # Filter by equipment
        if not require_equip:
            query = query.filter(Exercise.equipment.ilike("%Bodyweight%"))
            
        # Filter by tags (partial match)
        if isinstance(tags, list):
            pass 
        else:
             query = query.filter(Exercise.tags.ilike(f"%{tags}%"))
             
        candidates = query.all()
        
        # Filter strictly by muscle if requested
        if strict_muscle and primary_muscles:
             candidates = [c for c in candidates if any(m.lower() in (c.muscle_group or "").lower() for m in primary_muscles)]
             
        if not candidates: return []
        
        return random.sample(candidates, min(limit, len(candidates)))

    routine = []
    
    # PHASE 1: WARM-UP (2 Exercises)
    # Mobility, Light Cardio
    warmups = get_ex("warmup", 2)
    if not warmups: # Fallback query
        warmups = Exercise.query.filter(Exercise.tags.ilike("%mobility%")).limit(2).all()
    routine.extend([{"phase": "Warm-up", "data": w} for w in warmups])

    # PHASE 2: MAIN LIFT (7-11 Exercises)
    target_count = 10 if fitness_level == "beginner" else (12 if fitness_level == "intermediate" else 15)
    main_count = target_count - 4 # Reserve for other phases
    
    # Query Main Exercises
    main_query = Exercise.query.filter(Exercise.tags.notin_(["warmup", "cooldown", "stretch"]))
    if not require_equip:
         main_query = main_query.filter(Exercise.equipment.ilike("%Bodyweight%"))
    
    # Filter by difficulty approx
    all_main = main_query.all()
    
    # Scoping to muscle groups
    relevant_main = [e for e in all_main if any(m.lower() in (e.muscle_group or "").lower() for m in primary_muscles)]
    if len(relevant_main) < main_count:
        relevant_main = all_main # Fallback to all if not enough specific ones
        
    selected_main = random.sample(relevant_main, min(main_count, len(relevant_main)))
    routine.extend([{"phase": "Main Workout", "data": e} for e in selected_main])
    
    # PHASE 3: FINISHER (1-2 Exercises)
    # HIIT or Core
    finishers = get_ex("hiit", 1) or get_ex("abs", 1)
    routine.extend([{"phase": "Finisher", "data": f} for f in finishers])

    # PHASE 4: COOL-DOWN (1 Exercise)
    cooldowns = get_ex("stretch", 1)
    routine.extend([{"phase": "Cool-down", "data": c} for c in cooldowns])
    
    # Format Result
    formatted_routine = []
    for item in routine:
        ex = item["data"]
        # Smart Sets/Reps
        sets = 3
        reps = "10-12"
        if item["phase"] == "Warm-up": sets=1; reps="60 sec"
        elif item["phase"] == "Main Workout": 
            if "strength" in ex.tags: sets=4; reps="8-10"
            else: sets=3; reps="12-15"
        elif item["phase"] == "Finisher": sets=2; reps="Failure"
        elif item["phase"] == "Cool-down": sets=1; reps="60 sec hold"
        
        formatted_routine.append({
            "name": ex.name,
            "phase": item["phase"],
            "sets": sets,
            "reps": reps,
            "muscle_group": ex.muscle_group,
            "equipment": ex.equipment,
            "difficulty": ex.difficulty,
            "description": ex.description,
            "animation_url": ex.animation_url or "https://assets.lottiefiles.com/packages/lf20_9xRkZk.json",
            "thumbnail_url": ex.thumbnail_url or "https://placehold.co/100x100?text=Ex",
            "id": ex.id
        })
        
    return formatted_routine


def recommend_workout(goal: str, fitness_level: str, freq: int) -> Dict:
    """
    Legacy wrapper retained for compatibility, now uses generate_exercises_list.
    """
    # Simply generate one routine and package it
    # We default to requesting equipment if available in the app context, or just "with_equipment" logic
    exercises = generate_exercises_list(goal, fitness_level, "with_equipment")
    
    return {
        "goal": goal,
        "level": fitness_level,
        "exercises": exercises,
        "estimated_duration": f"{len(exercises) * 3} mins",
        "calories_burn": len(exercises) * 20
    }

def get_equipment_for_workout(exercises: List[Dict]) -> List[str]:
    """Extract required equipment from a list of exercises."""
    equipment = set()
    for ex in exercises:
        eq = ex.get("equipment", "Bodyweight")
        if eq and "Bodyweight" not in eq and "None" not in eq:
            # Clean up string "Dumbbells, Mat" -> ["Dumbbells", "Mat"]
            for item in eq.split(","):
                clean = item.strip()
                if clean: equipment.add(clean)
    return list(equipment)



def recommend_diet(weight: float, target: float, goal: str) -> Dict:
    """
    Recommend diet plan using Mifflin-St Jeor-like calculation.
    
    Args:
        weight: Current weight in kg
        target: Target weight in kg
        goal: Goal type (fat_loss, muscle_gain, recomposition)
    
    Returns:
        Dictionary with calories, macros, and summary
    """
    if weight is None or weight <= 0:
        weight = 70  # Default fallback
    
    goal_lower = (goal or "").lower()
    
    # Simplified Mifflin-St Jeor BMR estimation (using average values)
    # BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age + 5 (male) or -161 (female)
    # Using simplified: BMR ≈ weight * 22 (rough estimate for average person)
    base_bmr = weight * 22
    
    # Activity multiplier (assuming moderate activity)
    activity_multiplier = 1.55
    maintenance_calories = base_bmr * activity_multiplier
    
    # Adjust calories based on goal
    if goal_lower in ["fat_loss", "lose", "weight_loss"]:
        calories = maintenance_calories - 400  # Deficit for fat loss
    elif goal_lower in ["muscle_gain", "gain", "bulk"]:
        calories = maintenance_calories + 300  # Surplus for muscle gain
    elif goal_lower in ["recomposition", "recomp"]:
        calories = maintenance_calories - 100  # Slight deficit for recomposition
    else:
        calories = maintenance_calories
    
    # Macro calculations
    # Protein: 1.8-2.2g per kg bodyweight (use 2.0g for muscle gain, 1.8g otherwise)
    if goal_lower in ["muscle_gain", "gain", "bulk"]:
        protein_g = weight * 2.0
    else:
        protein_g = weight * 1.8
    
    # Fats: 0.8-1.0g per kg (use 1.0g for muscle gain, 0.8g for fat loss)
    if goal_lower in ["muscle_gain", "gain", "bulk"]:
        fats_g = weight * 1.0
    elif goal_lower in ["fat_loss", "lose", "weight_loss"]:
        fats_g = weight * 0.7  # Lower fat for fat loss
    else:
        fats_g = weight * 0.8
    
    # Carbs: remaining calories
    protein_cals = protein_g * 4
    fats_cals = fats_g * 9
    remaining_cals = calories - protein_cals - fats_cals
    carbs_g = max(0, remaining_cals / 4)
    
    # Generate summary
    goal_display = goal_lower.replace("_", " ").title() if goal_lower else "Balance"
    summary = (
        f"Daily target: {round(calories)} kcal to support {goal_display}. "
        f"Macros: {round(protein_g)}g protein, {round(carbs_g)}g carbs, {round(fats_g)}g fats. "
        f"Focus on {'high protein and carbs' if 'gain' in goal_lower else 'protein and controlled carbs' if 'lose' in goal_lower else 'balanced macros'}."
    )
    
    return {
        "calories": round(calories),
        "macros": {
            "protein_g": round(protein_g),
            "carbs_g": round(carbs_g),
            "fats_g": round(fats_g),
        },
        "summary": summary
    }


def generate_weekly_mealplan(diet: Dict, goal: str) -> List[Dict]:
    """
    Generate 7-day meal plan with breakfast, lunch, dinner, and snacks.
    
    Args:
        diet: Diet dictionary with calories and macros
        goal: Goal type for meal adjustments
    
    Returns:
        List of 7 daily meal plans
    """
    calories = diet.get("calories", 2000)
    protein_g = diet.get("macros", {}).get("protein_g", 120)
    carbs_g = diet.get("macros", {}).get("carbs_g", 200)
    fats_g = diet.get("macros", {}).get("fats_g", 70)
    
    goal_lower = (goal or "").lower()
    
    # Meal templates adjusted by goal
    if goal_lower in ["fat_loss", "lose", "weight_loss"]:
        # High protein, lower carb, clean foods
        meal_templates = [
            {
                "breakfast": "Greek yogurt with berries and almonds",
                "lunch": "Grilled chicken salad with olive oil dressing",
                "dinner": "Baked salmon with steamed vegetables",
                "snacks": "Protein shake, apple with peanut butter"
            },
            {
                "breakfast": "Scrambled eggs with spinach and whole grain toast",
                "lunch": "Turkey wrap with vegetables",
                "dinner": "Lean beef stir-fry with broccoli",
                "snacks": "Cottage cheese, mixed nuts"
            },
            {
                "breakfast": "Protein smoothie with banana and spinach",
                "lunch": "Tuna salad with mixed greens",
                "dinner": "Grilled chicken breast with quinoa and asparagus",
                "snacks": "Hard-boiled eggs, cucumber slices"
            },
            {
                "breakfast": "Oatmeal with protein powder and berries",
                "lunch": "Chicken and vegetable soup",
                "dinner": "Baked cod with sweet potato and green beans",
                "snacks": "Greek yogurt, almonds"
            },
            {
                "breakfast": "Egg white omelet with vegetables",
                "lunch": "Grilled chicken Caesar salad (light dressing)",
                "dinner": "Lean pork tenderloin with roasted vegetables",
                "snacks": "Protein bar, apple"
            },
            {
                "breakfast": "Cottage cheese with fruit and nuts",
                "lunch": "Salmon and quinoa bowl",
                "dinner": "Turkey meatballs with zucchini noodles",
                "snacks": "Protein shake, mixed berries"
            },
            {
                "breakfast": "Whole grain toast with avocado and poached eggs",
                "lunch": "Chicken and vegetable stir-fry",
                "dinner": "Grilled fish with brown rice and vegetables",
                "snacks": "Greek yogurt, trail mix"
            }
        ]
    elif goal_lower in ["muscle_gain", "gain", "bulk"]:
        # High protein, high carbs, calorie-dense foods
        meal_templates = [
            {
                "breakfast": "Oatmeal with protein powder, banana, and peanut butter",
                "lunch": "Chicken breast with rice and vegetables",
                "dinner": "Beef steak with potatoes and mixed vegetables",
                "snacks": "Protein shake, granola bar, nuts"
            },
            {
                "breakfast": "Scrambled eggs with bacon and whole grain toast",
                "lunch": "Pasta with ground turkey and marinara sauce",
                "dinner": "Salmon with sweet potato and broccoli",
                "snacks": "Greek yogurt with honey, protein bar"
            },
            {
                "breakfast": "Protein pancakes with syrup and berries",
                "lunch": "Chicken and rice bowl with avocado",
                "dinner": "Pork chops with mashed potatoes and green beans",
                "snacks": "Protein shake, banana, peanut butter"
            },
            {
                "breakfast": "Breakfast burrito with eggs, cheese, and sausage",
                "lunch": "Beef and rice stir-fry",
                "dinner": "Grilled chicken with pasta and vegetables",
                "snacks": "Trail mix, protein shake"
            },
            {
                "breakfast": "Greek yogurt parfait with granola and fruit",
                "lunch": "Turkey sandwich with whole grain bread",
                "dinner": "Baked cod with rice and vegetables",
                "snacks": "Protein bar, mixed nuts, apple"
            },
            {
                "breakfast": "Omelet with cheese, vegetables, and toast",
                "lunch": "Chicken and quinoa bowl",
                "dinner": "Lean beef with potatoes and asparagus",
                "snacks": "Protein shake, Greek yogurt, berries"
            },
            {
                "breakfast": "Protein smoothie bowl with toppings",
                "lunch": "Salmon with rice and vegetables",
                "dinner": "Pork tenderloin with sweet potato and broccoli",
                "snacks": "Protein bar, trail mix, banana"
            }
        ]
    else:  # recomposition or balanced
        # Balanced macros, clean foods
        meal_templates = [
            {
                "breakfast": "Greek yogurt with berries and granola",
                "lunch": "Grilled chicken with quinoa and vegetables",
                "dinner": "Baked salmon with sweet potato and greens",
                "snacks": "Protein shake, mixed nuts"
            },
            {
                "breakfast": "Scrambled eggs with whole grain toast and avocado",
                "lunch": "Turkey and vegetable wrap",
                "dinner": "Lean beef with brown rice and broccoli",
                "snacks": "Greek yogurt, apple"
            },
            {
                "breakfast": "Oatmeal with protein powder and fruit",
                "lunch": "Chicken salad with olive oil dressing",
                "dinner": "Grilled fish with quinoa and vegetables",
                "snacks": "Cottage cheese, almonds"
            },
            {
                "breakfast": "Protein smoothie with spinach and banana",
                "lunch": "Salmon and rice bowl",
                "dinner": "Chicken breast with sweet potato and asparagus",
                "snacks": "Hard-boiled eggs, mixed berries"
            },
            {
                "breakfast": "Whole grain toast with eggs and vegetables",
                "lunch": "Tuna salad with mixed greens",
                "dinner": "Pork tenderloin with brown rice and green beans",
                "snacks": "Protein bar, Greek yogurt"
            },
            {
                "breakfast": "Cottage cheese with fruit and nuts",
                "lunch": "Chicken and vegetable stir-fry",
                "dinner": "Baked cod with quinoa and vegetables",
                "snacks": "Protein shake, trail mix"
            },
            {
                "breakfast": "Egg white omelet with vegetables and cheese",
                "lunch": "Grilled chicken Caesar salad",
                "dinner": "Lean beef with potatoes and mixed vegetables",
                "snacks": "Greek yogurt, protein bar"
            }
        ]
    
    # Generate 7-day plan
    weekly_plan = []
    for day_num in range(7):
        day_plan = meal_templates[day_num % len(meal_templates)]
        weekly_plan.append({
            "day": day_num + 1,
            "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_num],
            "calories": round(calories),
            "macros": {
                "protein_g": round(protein_g),
                "carbs_g": round(carbs_g),
                "fats_g": round(fats_g),
            },
            "meals": {
                "breakfast": day_plan["breakfast"],
                "lunch": day_plan["lunch"],
                "dinner": day_plan["dinner"],
                "snacks": day_plan["snacks"]
            }
        })
    
    return weekly_plan


def recommend_shopping(goal: str, app=None) -> List[Dict]:
    """
    Recommend shopping products based on goal with smart affiliate links.
    """
    goal_lower = (goal or "").lower()
    
    # Goal to equipment/supplements mapping
    recommendations_map = {
        "fat_loss": ["skipping_rope", "resistance_bands", "yoga_mat", "whey_isolate", "smart_watch"],
        "muscle_gain": ["dumbbells", "creatine", "whey_protein", "weight_bench", "lifting_straps"],
        "body_recomp": ["adjustable_dumbbells", "yoga_mat", "protein_powder", "kettlebell"],
        "core_strength": ["ab_wheel", "sliders", "yoga_mat", "medicine_ball"],
        "flexibility": ["yoga_mat", "foam_roller", "yoga_blocks"]
    }
    
    # Default to full body / general
    target_items = recommendations_map.get(goal_lower, ["resistance_bands", "dumbbells", "yoga_mat", "water_bottle"])
    
    products_list = []
    
    # 1. Try DB matches first
    if app:
        try:
            with app.app_context():
                # Simple logic: partial name match or category match
                # For production, we'd have a tag system
                for item_key in target_items:
                    # Search by name similar to item key
                    match = Product.query.filter(Product.name.ilike(f"%{item_key.replace('_', ' ')}%")).first()
                    if match:
                        products_list.append({
                            "id": match.id,
                            "name": match.name,
                            "price": float(match.price),
                            "image_url": match.image_url or "https://placehold.co/200x200?text=GymSphere",
                            "rating": match.rating or 4.5,
                            "src": match.src or "local",
                            "affiliate_url": match.affiliate_url or "#"
                        })
        except Exception:
            pass
            
    # 2. Fill gaps with "Smart" defaults (Affiliate Placeholders)
    # If we didn't find enough items in DB, we generate them dynamically
    
    defaults_db = {
        "skipping_rope": {"name": "Pro Speed Rope", "price": 14.99, "img": "https://m.media-amazon.com/images/I/71q+9gE-cAL._AC_SX679_.jpg"},
        "resistance_bands": {"name": "Heavy Duty Bands Set", "price": 29.99, "img": "https://m.media-amazon.com/images/I/71D0-l-rMzL._AC_SX679_.jpg"},
        "yoga_mat": {"name": "Non-Slip Yoga Mat", "price": 45.00, "img": "https://m.media-amazon.com/images/I/81+6iM6C5XL._AC_SX679_.jpg"},
        "whey_isolate": {"name": "Gold Standard Whey", "price": 69.99, "img": "https://m.media-amazon.com/images/I/71+6P+H6+pL._AC_SX679_.jpg"},
        "smart_watch": {"name": "Fitness Tracker Pro", "price": 129.99, "img": "https://m.media-amazon.com/images/I/61s+N0+1sWL._AC_SX679_.jpg"},
        "dumbbells": {"name": "Hex Dumbbell Pair (10kg)", "price": 59.99, "img": "https://m.media-amazon.com/images/I/71ShRz-BcxL._AC_SX679_.jpg"},
        "creatine": {"name": "Micronized Creatine", "price": 24.99, "img": "https://m.media-amazon.com/images/I/71t+vO-4KqL._AC_SX679_.jpg"},
        "ab_wheel": {"name": "Core Roller", "price": 19.99, "img": "https://m.media-amazon.com/images/I/71-Wl6+FmTL._AC_SX679_.jpg"},
        "adjustable_dumbbells": {"name": "SelectTech Dumbbells", "price": 299.00, "img": "https://m.media-amazon.com/images/I/71+pOdQ7iKL._AC_SX679_.jpg"}
    }
    
    needed = 5 - len(products_list)
    if needed > 0:
        for item_key in target_items:
            if len(products_list) >= 6: break
            
            # If not already present
            if not any(p['name'].lower() in item_key.replace('_', ' ') for p in products_list):
                def_item = defaults_db.get(item_key, {"name": item_key.replace('_', ' ').title(), "price": 25.00, "img": ""})
                
                # Generate valid Amazon Search Link
                search_term = def_item["name"].replace(" ", "+")
                link = f"https://www.amazon.com/s?k={search_term}&tag=gymsphere-20"
                
                products_list.append({
                    "id": None,
                    "name": def_item["name"],
                    "price": def_item["price"],
                    "image_url": def_item["img"] or "https://placehold.co/200x200?text=Product",
                    "rating": 4.8,
                    "src": "amazon",
                    "affiliate_url": link
                })
                
    return products_list


# --- Smart Notification Engine ---

def create_notification(user, title, message, type="info", payload=None):
    """Helper to create and commit a notification."""
    try:
        n = Notification(
            user_id=user.id,
            title=title,
            message=message,
            type=type,
            payload_json=payload,
            created_at=datetime.utcnow()
        )
        db.session.add(n)
        db.session.commit()
        return n
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None

def check_notifications_engine(user: User) -> None:
    """
    Master function to check and generate all smart notifications.
    Should be called on dashboard load or via background job.
    """
    if not user: return

    # 1. Update & Check Streaks (Core Logic)
    streaks = calculate_streaks(user)
    
    # 2. Tomorrow's Plan (Evening Reminder)
    # Trigger after 6 PM
    if datetime.utcnow().hour >= 18:
        schedule_tomorrow_plan_notification(user)

    # 3. Morning Motivation (Daily)
    schedule_morning_reminder(user)

    # 4. Missed Workout Alert (Yesterday)
    check_missed_workout(user)

    # 5. Weekly Summary (Sunday Evening)
    if datetime.utcnow().weekday() == 6 and datetime.utcnow().hour >= 18:
        generate_weekly_summary(user)


def schedule_tomorrow_plan_notification(user: User):
    """Check tomorrow's plan and notify user."""
    from models import DailyPlanEntry, UserPlan
    
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    
    # Find active plan
    plan = UserPlan.query.filter(UserPlan.user_id == user.id, UserPlan.end_date >= tomorrow).first()
    if not plan: return

    entry = DailyPlanEntry.query.filter_by(plan_id=plan.id, date=tomorrow).first()
    if not entry: return

    title = "Tomorrow's Plan Ready 📅"
    if Notification.query.filter_by(user_id=user.id, title=title, is_read=False).first():
        return

    if entry.is_exercise_day:
        # Get first 2 exercises
        ex_names = [ex['name'] for ex in (entry.exercise_payload or [])[:2]]
        workout_preview = ", ".join(ex_names)
        msg = f"Tomorrow's Workout: {workout_preview} + more. Get ready!"
    else:
        msg = "Tomorrow is a Rest Day. Focus on recovery and nutrition."
        
    create_notification(user, title, msg, type="plan", payload={"date": str(tomorrow)})


def schedule_morning_reminder(user: User):
    """Daily AI Coach motivation."""
    today = datetime.utcnow().date()
    title = "Coach Update 🤖"
    
    # Only one per day
    if Notification.query.filter(
        Notification.user_id == user.id, 
        Notification.title == title,
        Notification.created_at >= datetime.utcnow().replace(hour=0, minute=0)
    ).first():
        return
    
    msg = get_ai_coach_message(user)
    create_notification(user, title, msg, type="motivation")


def check_missed_workout(user: User):
    """Check if yesterday's workout was missed."""
    from models import DailyPlanEntry, UserPlan
    
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    
    # active plan covering yesterday
    plan = UserPlan.query.filter(UserPlan.user_id == user.id, UserPlan.start_date <= yesterday).first()
    if not plan: return
    
    entry = DailyPlanEntry.query.filter_by(plan_id=plan.id, date=yesterday).first()
    
    # If it was exercise day, and NOT completed
    if entry and entry.is_exercise_day and not entry.is_exercise_completed:
        title = "Missed Workout ⚠️"
        if not Notification.query.filter_by(user_id=user.id, title=title, created_at=yesterday).first():
             create_notification(user, title, "You missed yesterday's workout. Don't let it break your momentum! Get back on track today.", type="alert")


def get_ai_coach_message(user: User) -> str:
    """Generate rule-based AI coach message."""
    import random
    
    streak = user.workout_streak
    
    if streak > 5:
        return random.choice([
            f"Unstoppable! {streak} day streak. You're building a new version of yourself.",
            "Consistency is your superpower. Keep this streak alive!",
            "You are crushing it. Remember why you started."
        ])
    elif streak > 2:
        return random.choice([
            "Great momentum! Keep pushing.",
            "You're doing great. Stay focused today.",
            "Another day, another opportunity to improve."
        ])
    else:
        return random.choice([
            "The hardest part is showing up. You got this!",
            "Small steps every day lead to big results.",
            "Don't give up. Consistency beats intensity.",
            "Let's make today count!"
        ])






def generate_weekly_summary(user):
    """
    Weekly summary notification.
    """
    # Logic in weekly_progress_check handles this mostly
    weekly_progress_check(user)


# --- Plan Generators (Preserved) ---


def recommend_workout_day(goal: str, fitness_level: str, day_index: int, is_break: bool) -> List[Dict]:
    """
    Recommend exercises for a specific day in the plan.
    Rotates muscle groups: Push, Pull, Legs, Core, Full Body.
    """
    if is_break:
        return []

    # Simple rotation based on day index (0-based)
    # 0=Push, 1=Pull, 2=Legs, 3=Core, 4=Full Body
    rotation = ["muscle_gain", "back", "legs", "abs", "fat_loss"]
    day_type = rotation[day_index % len(rotation)]
    
    # We use the existing logic to get a full plan, then extract exercises
    pseudo_goal = day_type
    if pseudo_goal == "back": pseudo_goal = "muscle_gain" 
    if pseudo_goal == "legs": pseudo_goal = "muscle_gain" 
    
    plan = recommend_workout(pseudo_goal, fitness_level, 7) # Get ample exercises
    exercises = plan.get("exercises", [])
    
    # Shuffle or rotate based on day to add variety (simple slice shift)
    shift = day_index % max(1, len(exercises))
    exercises = exercises[shift:] + exercises[:shift]
    
    return exercises[:5] # Return top 5 for the day


def recommend_meals_for_day(calories: int, macros: Dict, preference: str, goal: str, day_index: int) -> Dict:
    """
    Generate a full day of eating based on calories/macros and preferences.
    """
    # Base templates
    is_nonveg = preference == "nonveg" or preference == "mixed"
    
    # Helper to generate meal string
    def get_meal(type_name):
        base = ""
        if type_name == "breakfast":
            if is_nonveg and goal == "muscle_gain":
                base = "Omelette with spinach & turkey bacon, oatmeal"
            else:
                base = "Greek yogurt parfait with berries & granola"
        elif type_name == "lunch":
            if is_nonveg:
                base = "Grilled chicken breast, quinoa, roasted veggies"
            else:
                base = "Lentil soup, brown rice, avocado salad"
        elif type_name == "dinner":
            if is_nonveg:
                base = "Baked salmon/fish, sweet potato, steamed broccoli"
            else:
                base = "Tofu stir-fry with mixed vegetables"
        elif type_name == "snacks":
            base = "Protein shake, almonds, apple"
        
        variations = [" (Option A)", " (Option B)", " (Spicy)", " (Herbal)"]
        return base + variations[day_index % 4]

    return {
        "calories": calories,
        "protein_g": macros.get("protein_g"),
        "carbs_g": macros.get("carbs_g"),
        "fats_g": macros.get("fats_g"),
        "meals": {
            "breakfast": get_meal("breakfast"),
            "lunch": get_meal("lunch"),
            "dinner": get_meal("dinner"),
            "snacks": get_meal("snacks")
        },
        "note": f"Focus on hitting ~{macros.get('protein_g')}g protein today."
    }


def generate_month_plan(user: User, start_date: Optional[str] = None) -> Optional["UserPlan"]:
    """
    Generate a 30-day workout and diet plan.
    """
    from models import UserPlan, DailyPlanEntry  # Local import
    
    if not start_date:
        start_date_obj = datetime.utcnow().date()
    else:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except:
            start_date_obj = datetime.utcnow().date()

    goal = user.goal or "maintain"
    fitness_level = user.fitness_level or "beginner"
    preference = "nonveg" # Default preference
    
    diet_info = recommend_diet(user.weight_kg, user.target_weight_kg, goal)
    calories = diet_info["calories"]
    macros = diet_info["macros"]

    plan = UserPlan(
        user_id=user.id,
        plan_type="workout+diet",
        goal=goal,
        preference=preference,
        start_date=start_date_obj,
        end_date=start_date_obj + timedelta(days=29),
        frequency_per_week=5,
        fitness_level=fitness_level,
        metadata_json={"total_days": 30}
    )
    
    entries = []
    
    for i in range(30):
        current_date = start_date_obj + timedelta(days=i)
        
        # Rule: Every 3rd day is a Rest Day (Day 3, 6, 9...)
        is_break = ((i + 1) % 3 == 0)
            
        diet_payload = recommend_meals_for_day(calories, macros, preference, goal, i)
        
        exercise_payload = []
        if not is_break:
            exercise_payload = recommend_workout_day(goal, fitness_level, i, is_break)
        
        entry = DailyPlanEntry(
            date=current_date,
            is_exercise_day=not is_break,
            exercise_payload=exercise_payload,
            diet_payload=diet_payload,
            streak_group=1
        )
        entries.append(entry)
    
    plan.daily_entries = entries
    
    db.session.add(plan)
    db.session.commit()
    return plan


def calculate_streaks(user: User) -> Dict:
    """
    Calculate and update user streaks (Workout & Diet).
    Rules:
    - Workout Streak: Consecutive days of exercise. Rest days count if not missed.
      If missed, streak resets.
    - Diet Streak: Consecutive days of diet completion.
    """
    from models import DailyPlanEntry, UserPlan
    
    if not user: return {"workout": 0, "diet": 0}

    # Find active or latest plan
    plan = UserPlan.query.filter_by(user_id=user.id).order_by(UserPlan.created_at.desc()).first()
    if not plan: return {"workout": 0, "diet": 0}
    
    today = datetime.utcnow().date()
    
    # Fetch entries up to yesterday (Streaks are usually built on past completetion)
    # But for "Current Streak" we include today if done.
    
    entries = DailyPlanEntry.query.filter_by(plan_id=plan.id).filter(DailyPlanEntry.date <= today).order_by(DailyPlanEntry.date.desc()).all()
    
    w_streak = 0
    d_streak = 0
    
    # 1. Calculate Workout Streak
    # Look for unbroken chain from today/yesterday backwards
    # If today is NOT done yet, we start looking from yesterday.
    
    # Helper to check if day is "valid" for streak
    # Valid = (Exercise Done) OR (Rest Day)
    # Invalid = (Exercise Day AND Not Done)
    
    current_idx = 0
    if not entries: return {"workout": 0, "diet": 0}
    
    # Handle Today: If not done, it doesn't break streak yet, just doesn't add to it.
    # Unless it's already past interaction time? simpler:
    # If today done -> include. If today not done -> start checking from yesterday.
    
    first_entry = entries[0]
    start_check_idx = 0
    
    if first_entry.date == today:
        workout_done = (first_entry.is_exercise_day and first_entry.is_exercise_completed) or (not first_entry.is_exercise_day)
        diet_done = first_entry.is_diet_completed
        
        if workout_done:
            w_streak += 1
        elif first_entry.is_exercise_day and not first_entry.is_exercise_completed:
            # If today is exercise day and not done, it doesn't break streak from yesterday
            pass 
        
        if diet_done:
            d_streak += 1
        
        start_check_idx = 1 # Continue to yesterday
    
    # Iterate backwards
    for i in range(start_check_idx, len(entries)):
        e = entries[i]
        
        # Workout Logic
        # Rest days maintain streak
        is_success_w = (e.is_exercise_day and e.is_exercise_completed) or (not e.is_exercise_day)
        
        # Check gap between dates? We assume entries are contiguous days.
        # If there's a date gap, streak breaks.
        expected_date = today - timedelta(days=i) # Approximate
        # We should check date continuity if strictly needed, but let's assume entries exist for every day in plan
        
        if is_success_w:
            w_streak += 1
        else:
            break
            
    # 2. Calculate Diet Streak
    # Iterate backwards again
    w_streak_temp = w_streak # Save it
    
    # Reset for diet
    # Logic: Diet must be done every day
    # Continue from where we left off or restart loop? Restart loop is clearer
    
    # Simple Diet Loop
    d_streak_count = 0
    # Check today again for diet
    if entries[0].date == today and entries[0].is_diet_completed:
        d_streak_count = 1
    
    # Backwards from yesterday
    for i in range(1 if entries[0].date == today else 0, len(entries)):
        e = entries[i]
        if e.is_diet_completed:
            d_streak_count += 1
        else:
            break
            
    # Update User Model
    if w_streak_temp != user.workout_streak or d_streak_count != user.diet_streak:
        user.workout_streak = w_streak_temp
        user.diet_streak = d_streak_count
        db.session.commit()
    
    # Streak Badges?
    # Could be added here
    
    return {"workout": w_streak_temp, "diet": d_streak_count}


def compute_streaks(user_id: int, plan_id: int) -> Dict:
    """Wrapper for backward compatibility."""
    user = User.query.get(user_id)
    return calculate_streaks(user)
