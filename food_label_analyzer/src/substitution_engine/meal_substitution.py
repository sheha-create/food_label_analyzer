"""
Meal Context Substitution Simulator
Evaluates substitutions within breakfast, lunch, dinner, and snack contexts
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from food_label_analyzer.src.config import UserProfile
    from food_label_analyzer.src.data_loader import FoodData, get_data_loader
    from food_label_analyzer.src.substitution_engine.advanced_recommender import AdvancedSubstitutionEngine, SubstituteScore
except ImportError:
    from src.config import UserProfile
    from src.data_loader import FoodData, get_data_loader
    from src.substitution_engine.advanced_recommender import AdvancedSubstitutionEngine, SubstituteScore


class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


@dataclass
class MealSubstitutionResult:
    """Result of meal substitution analysis"""
    meal_type: MealType
    original_foods: List[FoodData]
    substitutions: Dict[str, SubstituteScore]  # original_food_id -> best_substitute
    
    # Original meal totals
    original_calories: float
    original_sugars: float
    original_sodium: float
    original_carbs: float
    original_fiber: float
    original_health_score: float
    
    # Substituted meal totals
    substituted_calories: float
    substituted_sugars: float
    substituted_sodium: float
    substituted_carbs: float
    substituted_fiber: float
    substituted_health_score: float
    
    # Improvements
    calorie_reduction_pct: float = 0.0
    sugar_reduction_pct: float = 0.0
    sodium_reduction_pct: float = 0.0
    fiber_increase_pct: float = 0.0
    health_improvement: float = 0.0


class MealContextSimulator:
    """Simulate meal-level substitutions"""
    
    # Meal type food preferences
    MEAL_TYPE_PREFERENCES = {
        MealType.BREAKFAST: ['Grain', 'Dairy', 'Fruit', 'Beverage'],
        MealType.LUNCH: ['Protein', 'Vegetable', 'Grain', 'IndianFood'],
        MealType.DINNER: ['Protein', 'Vegetable', 'Grain', 'IndianFood'],
        MealType.SNACK: ['Fruit', 'Nut', 'Snack', 'Beverage'],
    }
    
    def __init__(self):
        self.engine = AdvancedSubstitutionEngine()
        self.data_loader = get_data_loader()
    
    def simulate_meal_substitution(
        self, meal_type: MealType, foods: List[FoodData],
        user: UserProfile, substitutions_per_food: int = 1
    ) -> MealSubstitutionResult:
        """
        Simulate substituting foods in a meal
        
        Args:
            meal_type: Type of meal (breakfast, lunch, etc.)
            foods: List of foods in the meal
            user: User profile
            substitutions_per_food: Number of substitution options per food
            
        Returns:
            MealSubstitutionResult with original and substituted totals
        """
        # Calculate original meal totals
        original_calories = sum(f.calories for f in foods)
        original_sugars = sum(f.sugars_g for f in foods)
        original_sodium = sum(f.sodium_mg for f in foods)
        original_carbs = sum(f.carbs_g for f in foods)
        original_fiber = sum(f.fiber_g for f in foods)
        original_health_score = sum(
            self.engine.calculate_health_score(f, user) for f in foods
        ) / len(foods) if foods else 0.0
        
        # Find substitutions
        substitutions = {}
        substituted_foods = {}
        
        for food in foods:
            # Get top substitute for this food
            candidates = self.engine.find_substitutes(
                food, user, top_n=1, 
                exclude_categories=[]
            )
            
            if candidates:
                best_substitute = candidates[0]
                substitutions[food.food_id] = best_substitute
                
                # Get the actual substitute food object
                substitute_food = self.data_loader.get_food_by_id(best_substitute.food_id)
                if substitute_food:
                    substituted_foods[food.food_id] = substitute_food
            else:
                # No substitute found, keep original
                substituted_foods[food.food_id] = food
        
        # Calculate substituted meal totals
        substituted_items = list(substituted_foods.values())
        substituted_calories = sum(f.calories for f in substituted_items)
        substituted_sugars = sum(f.sugars_g for f in substituted_items)
        substituted_sodium = sum(f.sodium_mg for f in substituted_items)
        substituted_carbs = sum(f.carbs_g for f in substituted_items)
        substituted_fiber = sum(f.fiber_g for f in substituted_items)
        substituted_health_score = sum(
            self.engine.calculate_health_score(f, user) for f in substituted_items
        ) / len(substituted_items) if substituted_items else 0.0
        
        # Calculate improvements
        calorie_reduction_pct = (
            (original_calories - substituted_calories) / max(original_calories, 1) * 100
        )
        sugar_reduction_pct = (
            (original_sugars - substituted_sugars) / max(original_sugars, 0.1) * 100
        )
        sodium_reduction_pct = (
            (original_sodium - substituted_sodium) / max(original_sodium, 1) * 100
        )
        fiber_increase_pct = (
            (substituted_fiber - original_fiber) / max(original_fiber, 0.1) * 100
        )
        health_improvement = substituted_health_score - original_health_score
        
        return MealSubstitutionResult(
            meal_type=meal_type,
            original_foods=foods,
            substitutions=substitutions,
            original_calories=original_calories,
            original_sugars=original_sugars,
            original_sodium=original_sodium,
            original_carbs=original_carbs,
            original_fiber=original_fiber,
            original_health_score=original_health_score,
            substituted_calories=substituted_calories,
            substituted_sugars=substituted_sugars,
            substituted_sodium=substituted_sodium,
            substituted_carbs=substituted_carbs,
            substituted_fiber=substituted_fiber,
            substituted_health_score=substituted_health_score,
            calorie_reduction_pct=calorie_reduction_pct,
            sugar_reduction_pct=sugar_reduction_pct,
            sodium_reduction_pct=sodium_reduction_pct,
            fiber_increase_pct=fiber_increase_pct,
            health_improvement=health_improvement
        )
    
    def simulate_daily_meals(
        self, meals: Dict[MealType, List[FoodData]], user: UserProfile
    ) -> Dict[MealType, MealSubstitutionResult]:
        """Simulate substitutions across all meals in a day"""
        results = {}
        
        for meal_type, foods in meals.items():
            if foods:
                results[meal_type] = self.simulate_meal_substitution(
                    meal_type, foods, user
                )
        
        return results
    
    def get_daily_improvement_summary(
        self, meal_results: Dict[MealType, MealSubstitutionResult]
    ) -> Dict[str, any]:
        """Summarize improvements across all meals"""
        total_original_calories = sum(r.original_calories for r in meal_results.values())
        total_substituted_calories = sum(r.substituted_calories for r in meal_results.values())
        
        total_original_sugar = sum(r.original_sugars for r in meal_results.values())
        total_substituted_sugar = sum(r.substituted_sugars for r in meal_results.values())
        
        total_original_sodium = sum(r.original_sodium for r in meal_results.values())
        total_substituted_sodium = sum(r.substituted_sodium for r in meal_results.values())
        
        total_original_fiber = sum(r.original_fiber for r in meal_results.values())
        total_substituted_fiber = sum(r.substituted_fiber for r in meal_results.values())
        
        avg_original_health = sum(r.original_health_score for r in meal_results.values()) / len(meal_results)
        avg_substituted_health = sum(r.substituted_health_score for r in meal_results.values()) / len(meal_results)
        
        return {
            'total_calories_reduction_pct': (
                (total_original_calories - total_substituted_calories) / 
                max(total_original_calories, 1) * 100
            ),
            'total_sugar_reduction_pct': (
                (total_original_sugar - total_substituted_sugar) / 
                max(total_original_sugar, 0.1) * 100
            ),
            'total_sodium_reduction_pct': (
                (total_original_sodium - total_substituted_sodium) / 
                max(total_original_sodium, 1) * 100
            ),
            'total_fiber_increase_pct': (
                (total_substituted_fiber - total_original_fiber) / 
                max(total_original_fiber, 0.1) * 100
            ),
            'health_score_improvement': avg_substituted_health - avg_original_health,
            'meals_improved': len(meal_results),
        }
