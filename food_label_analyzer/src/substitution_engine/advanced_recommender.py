"""
Advanced Substitution Ranking Engine
Implements weighted scoring formula with goal-based personalization
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from pathlib import Path

try:
    from food_label_analyzer.src.config import UserProfile, UserGoal, DietaryPreference
    from food_label_analyzer.src.data_loader import FoodData, get_data_loader
except ImportError:
    from src.config import UserProfile, UserGoal, DietaryPreference
    from src.data_loader import FoodData, get_data_loader


@dataclass
class SubstituteScore:
    """Score details for a substitute recommendation"""
    food_id: str
    food_name: str
    category: str
    total_score: float
    
    # Component scores
    sugar_score: float
    net_carbs_score: float
    gi_score: float
    sodium_score: float
    calorie_score: float
    similarity_score: float
    
    # Nutritional deltas (vs original)
    sugar_delta_g: float
    net_carbs_delta_g: float
    gi_delta: float
    sodium_delta_mg: float
    calorie_delta: float
    
    # Recommendation details
    health_score_original: float = 0.0
    health_score_substitute: float = 0.0
    reasoning: str = ""
    badges: List[str] = None
    
    def __post_init__(self):
        if self.badges is None:
            self.badges = []


class AdvancedSubstitutionEngine:
    """Advanced substitution ranking with weighted scoring"""
    
    # Category mappings for similarity
    CATEGORY_GROUPS = {
        'Grain': ['Grain', 'Bread', 'Cereal'],
        'Fruit': ['Fruit', 'Beverage'],
        'Vegetable': ['Vegetable'],
        'Protein': ['Protein', 'Legume', 'Nut'],
        'Dairy': ['Dairy'],
        'Snack': ['Snack', 'Dessert'],
        'FastFood': ['FastFood'],
        'Beverage': ['Beverage', 'Fruit'],
        'IndianFood': ['IndianFood', 'Grain'],
    }
    
    # GI estimation by category (when not in database)
    GI_BY_CATEGORY = {
        'Grain': 65,
        'Bread': 70,
        'Cereal': 75,
        'Fruit': 50,
        'Vegetable': 35,
        'Protein': 25,
        'Legume': 28,
        'Nut': 20,
        'Dairy': 40,
        'Snack': 65,
        'Dessert': 60,
        'FastFood': 70,
        'Beverage': 55,
        'IndianFood': 60,
    }
    
    # Indian food GI overrides (more accurate values)
    INDIAN_FOOD_GI_OVERRIDES = {
        'dosa': 55,
        'samosa': 70,
        'chapati': 52,
        'rice with curry': 60,
        'biryani': 67,
        'naan': 63,
        'paneer curry': 35,
        'masala dosa': 58,
        'idli': 46,
        'gulab jamun': 70,
    }
    
    def __init__(self):
        self.data_loader = get_data_loader()
        self.weights = {
            'sugar': 0.25,
            'net_carbs': 0.20,
            'gi': 0.15,
            'sodium': 0.15,
            'calorie': 0.10,
            'similarity': 0.15,
        }
    
    def set_goal_weights(self, goal: UserGoal) -> Dict[str, float]:
        """Adjust weights based on user goal"""
        base_weights = self.weights.copy()
        
        if goal == UserGoal.LOW_SUGAR:
            base_weights['sugar'] = 0.40
            base_weights['net_carbs'] = 0.15
            base_weights['gi'] = 0.15
        elif goal == UserGoal.LOW_SODIUM:
            base_weights['sodium'] = 0.40
            base_weights['sugar'] = 0.15
            base_weights['net_carbs'] = 0.15
        elif goal == UserGoal.LOW_CALORIES:
            base_weights['calorie'] = 0.40
            base_weights['sugar'] = 0.10
            base_weights['sodium'] = 0.10
        elif goal == UserGoal.HIGH_PROTEIN:
            base_weights['protein'] = 0.30
            base_weights['calorie'] = 0.15
            base_weights['sugar'] = 0.15
        elif goal == UserGoal.HIGH_FIBER:
            base_weights['fiber'] = 0.30
            base_weights['carbs'] = 0.15
            base_weights['sugar'] = 0.15
        
        return base_weights
    
    def calculate_net_carbs(self, total_carbs: float, fiber: float) -> float:
        """Calculate net carbs = total carbs - fiber"""
        return max(0, total_carbs - fiber)
    
    def get_gi_for_food(self, food: FoodData) -> float:
        """Get GI for food with multiple fallbacks"""
        food_name_lower = food.food_name.lower()
        
        # Check Indian food overrides
        for food_key, gi_value in self.INDIAN_FOOD_GI_OVERRIDES.items():
            if food_key in food_name_lower:
                return float(gi_value)
        
        # Check main GI database
        gi = self.data_loader.get_gi_for_food(food.food_name)
        if gi is not None:
            return float(gi)
        
        # Fallback to category-based estimation
        category_gi = self.GI_BY_CATEGORY.get(food.category, 60)
        return float(category_gi)
    
    def get_category_group(self, category: str) -> str:
        """Get category group for similarity matching"""
        for group, categories in self.CATEGORY_GROUPS.items():
            if category in categories:
                return group
        return category
    
    def is_similar_category(self, cat1: str, cat2: str) -> bool:
        """Check if categories are in same group"""
        return self.get_category_group(cat1) == self.get_category_group(cat2)
    
    def score_nutritional_component(
        self, original_value: float, substitute_value: float, 
        lower_is_better: bool = True
    ) -> float:
        """Score improvement on single nutrient (0-1, higher is better)"""
        if lower_is_better:
            delta = original_value - substitute_value
            if original_value == 0:
                return 0.5 if delta == 0 else (1.0 if delta > 0 else 0.0)
            improvement_pct = delta / original_value
            return min(1.0, max(0.0, improvement_pct + 0.5))  # Scale to 0-1
        else:
            delta = substitute_value - original_value
            if original_value == 0:
                return 0.5 if delta == 0 else (1.0 if delta > 0 else 0.0)
            improvement_pct = delta / original_value
            return min(1.0, max(0.0, improvement_pct + 0.5))
    
    def calculate_similarity(self, original: FoodData, substitute: FoodData) -> float:
        """Calculate similarity score (0-1)"""
        score = 0.0
        
        # Category similarity
        if self.is_similar_category(original.category, substitute.category):
            score += 0.5
        
        # Serving size similarity
        size_ratio = min(original.serving_size_g, substitute.serving_size_g) / \
                     max(original.serving_size_g, substitute.serving_size_g)
        score += size_ratio * 0.3
        
        # Taste profile (simplistic: based on macros)
        carb_ratio = min(original.carbs_g, substitute.carbs_g) / \
                     max(original.carbs_g, substitute.carbs_g + 0.1)
        score += carb_ratio * 0.2
        
        return min(1.0, score)
    
    def calculate_health_score(self, food: FoodData, user: Optional[UserProfile] = None) -> float:
        """Calculate overall health score (0-100) for a food"""
        score = 50.0  # Base score
        
        # Nutritional factors
        net_carbs = self.calculate_net_carbs(food.carbs_g, food.fiber_g)
        gi = self.get_gi_for_food(food)
        
        # Sugar impact
        if food.sugars_g < 5:
            score += 15
        elif food.sugars_g < 10:
            score += 8
        elif food.sugars_g > 20:
            score -= 10
        
        # Fiber impact
        if food.fiber_g > 5:
            score += 12
        elif food.fiber_g > 2:
            score += 6
        
        # GI impact (for diabetes)
        if gi < 55:
            score += 10
        elif gi > 70:
            score -= 8
        
        # Sodium impact
        if food.sodium_mg < 200:
            score += 8
        elif food.sodium_mg > 800:
            score -= 10
        
        # Protein impact
        if food.protein_g > 15:
            score += 10
        elif food.protein_g > 5:
            score += 5
        
        return min(100, max(0, score))
    
    def find_substitutes(
        self, original_food: FoodData, user: UserProfile,
        top_n: int = 5, exclude_categories: List[str] = None
    ) -> List[SubstituteScore]:
        """
        Find top N substitutes using weighted scoring
        
        Args:
            original_food: Food to find substitutes for
            user: User profile with goals and preferences
            top_n: Number of top results to return
            exclude_categories: Categories to exclude
            
        Returns:
            Sorted list of SubstituteScore objects
        """
        if exclude_categories is None:
            exclude_categories = []
        
        # Get weights based on user goal
        weights = self.set_goal_weights(user.primary_goal)
        
        # Get all foods
        all_foods = self.data_loader.get_all_foods()
        
        # Get original food metrics
        original_net_carbs = self.calculate_net_carbs(original_food.carbs_g, original_food.fiber_g)
        original_gi = self.get_gi_for_food(original_food)
        original_health_score = self.calculate_health_score(original_food, user)
        
        scores = []
        
        for candidate in all_foods:
            # Skip original and excluded categories
            if candidate.food_id == original_food.food_id:
                continue
            if candidate.category in exclude_categories:
                continue
            
            # Category constraint: prefer same or similar category
            if not self.is_similar_category(original_food.category, candidate.category):
                continue
            
            # Calculate component scores
            candidate_net_carbs = self.calculate_net_carbs(candidate.carbs_g, candidate.fiber_g)
            candidate_gi = self.get_gi_for_food(candidate)
            candidate_health_score = self.calculate_health_score(candidate, user)
            
            sugar_score = self.score_nutritional_component(
                original_food.sugars_g, candidate.sugars_g, lower_is_better=True
            )
            net_carbs_score = self.score_nutritional_component(
                original_net_carbs, candidate_net_carbs, lower_is_better=True
            )
            gi_score = self.score_nutritional_component(
                original_gi, candidate_gi, lower_is_better=True
            )
            sodium_score = self.score_nutritional_component(
                original_food.sodium_mg, candidate.sodium_mg, lower_is_better=True
            )
            calorie_score = self.score_nutritional_component(
                original_food.calories, candidate.calories, lower_is_better=True
            )
            similarity_score = self.calculate_similarity(original_food, candidate)
            
            # Calculate weighted total score
            total_score = (
                weights['sugar'] * sugar_score +
                weights['net_carbs'] * net_carbs_score +
                weights['gi'] * gi_score +
                weights['sodium'] * sodium_score +
                weights['calorie'] * calorie_score +
                weights['similarity'] * similarity_score
            )
            
            # Calculate deltas
            sugar_delta = original_food.sugars_g - candidate.sugars_g
            net_carbs_delta = original_net_carbs - candidate_net_carbs
            gi_delta = original_gi - candidate_gi
            sodium_delta = original_food.sodium_mg - candidate.sodium_mg
            calorie_delta = original_food.calories - candidate.calories
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                original_food, candidate, sugar_delta, net_carbs_delta,
                gi_delta, sodium_delta, calorie_delta, user.primary_goal
            )
            
            # Generate badges
            badges = self._generate_badges(candidate, user)
            
            score_obj = SubstituteScore(
                food_id=candidate.food_id,
                food_name=candidate.food_name,
                category=candidate.category,
                total_score=total_score,
                sugar_score=sugar_score,
                net_carbs_score=net_carbs_score,
                gi_score=gi_score,
                sodium_score=sodium_score,
                calorie_score=calorie_score,
                similarity_score=similarity_score,
                sugar_delta_g=sugar_delta,
                net_carbs_delta_g=net_carbs_delta,
                gi_delta=gi_delta,
                sodium_delta_mg=sodium_delta,
                calorie_delta=calorie_delta,
                health_score_original=original_health_score,
                health_score_substitute=candidate_health_score,
                reasoning=reasoning,
                badges=badges
            )
            scores.append(score_obj)
        
        # Sort by total score descending
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores[:top_n]
    
    def _generate_reasoning(
        self, original: FoodData, substitute: FoodData,
        sugar_delta: float, net_carbs_delta: float, gi_delta: float,
        sodium_delta: float, calorie_delta: float, goal: UserGoal
    ) -> str:
        """Generate human-readable explanation"""
        reasons = []
        
        if sugar_delta > 2:
            reasons.append(f"{sugar_delta:.1f}g less sugar ({int(sugar_delta/max(original.sugars_g, 0.1)*100)}% reduction)")
        if net_carbs_delta > 3:
            reasons.append(f"{net_carbs_delta:.1f}g fewer net carbs")
        if gi_delta > 5:
            reasons.append(f"Lower GI by {gi_delta:.0f} points")
        if sodium_delta > 100:
            reasons.append(f"{int(sodium_delta)}mg less sodium")
        if calorie_delta > 20:
            reasons.append(f"{int(calorie_delta)} fewer calories")
        
        if not reasons:
            reasons.append("Similar nutritional profile with better health score")
        
        return "✓ " + ", ".join(reasons[:3])
    
    def _generate_badges(self, food: FoodData, user: UserProfile) -> List[str]:
        """Generate nutritional badges"""
        badges = []
        
        # Sugar badges
        if food.sugars_g < 5:
            badges.append("🟢 Low Sugar")
        elif food.sugars_g > 15:
            badges.append("🔴 High Sugar")
        
        # Fiber badges
        if food.fiber_g > 5:
            badges.append("🟢 High Fiber")
        elif food.fiber_g < 2:
            badges.append("🟡 Low Fiber")
        
        # Sodium badges
        if food.sodium_mg < 200:
            badges.append("🟢 Low Sodium")
        elif food.sodium_mg > 800:
            badges.append("🔴 High Sodium")
        
        # Protein badges
        if food.protein_g > 15:
            badges.append("💪 High Protein")
        
        # Diabetes-specific badges
        if user.has_diabetes:
            net_carbs = self.calculate_net_carbs(food.carbs_g, food.fiber_g)
            gi = self.get_gi_for_food(food)
            if food.sugars_g < 8 and gi < 60 and net_carbs < 20:
                badges.append("✅ Diabetic Friendly")
            elif food.sugars_g > 15 or gi > 75:
                badges.append("⚠️ Not for Diabetics")
        
        # Hypertension-specific badges
        if user.hypertension_severity.value != 'normal':
            if food.sodium_mg < 200:
                badges.append("✅ Hypertension Safe")
            elif food.sodium_mg > 1000:
                badges.append("⚠️ Not for Hypertension")
        
        return badges
