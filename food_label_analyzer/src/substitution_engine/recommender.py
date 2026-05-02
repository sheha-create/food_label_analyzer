"""
Substitution Engine - Recommends healthier food alternatives
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import field
import math
try:
    from food_label_analyzer.src.config import (
        FoodItem, SubstitutionRecommendation, UserProfile, FoodClassification,
    )
except ImportError:
    from src.config import (
        FoodItem, SubstitutionRecommendation, UserProfile, FoodClassification,
    )


class NutrientSimilarityMatcher:
    """Match foods based on nutritional similarity"""
    
    def __init__(self):
        # Weights for different nutrient considerations
        self.weights = {
            'serving_size': 0.1,
            'calories': 0.15,
            'carbs': 0.2,
            'protein': 0.15,
            'fat': 0.1,
            'fiber': 0.15,
            'sugar': 0.15,
        }
    
    def calculate_similarity(self, food1: FoodItem, food2: FoodItem) -> float:
        """
        Calculate nutritional similarity between two foods (0-1)
        
        Args:
            food1: Original food
            food2: Potential substitute
            
        Returns:
            Similarity score (0=very different, 1=very similar)
        """
        n1 = food1.nutrition_facts
        n2 = food2.nutrition_facts
        
        # Normalize serving sizes to 100g equivalent
        def normalize_to_100g(nutrition):
            scale = 100 / (nutrition.serving_size_grams or 100)
            return {
                'serving_size': nutrition.serving_size_grams,
                'calories': nutrition.calories * scale,
                'carbs': nutrition.total_carbs_g * scale,
                'protein': nutrition.protein_g * scale,
                'fat': nutrition.total_fat_g * scale,
                'fiber': nutrition.dietary_fiber_g * scale,
                'sugar': nutrition.sugars_g * scale,
            }
        
        norm1 = normalize_to_100g(n1)
        norm2 = normalize_to_100g(n2)
        
        # Calculate similarity for each nutrient
        similarities = {}
        
        for nutrient, weight in self.weights.items():
            v1 = norm1[nutrient]
            v2 = norm2[nutrient]
            
            if nutrient == 'serving_size':
                # For serving size, higher similarity if closer
                diff_percent = abs(v1 - v2) / max(v1, v2, 1) * 100
                similarities[nutrient] = max(0, 1 - diff_percent / 100)
            else:
                # For nutrients, calculate % difference
                if max(v1, v2) > 0:
                    diff = abs(v1 - v2) / max(v1, v2)
                    similarities[nutrient] = 1 - min(1, diff)
                else:
                    similarities[nutrient] = 1.0
        
        # Weighted average
        total_similarity = sum(similarities[n] * self.weights[n] 
                             for n in similarities if n in self.weights)
        
        return round(total_similarity, 3)
    
    def calculate_health_improvement(self, original: FoodItem, 
                                    substitute: FoodItem, 
                                    user_profile: Optional[UserProfile] = None) -> Dict:
        """
        Calculate health improvement from substitution
        
        Args:
            original: Original food
            substitute: Substitute food
            user_profile: Optional user profile for personalized scoring
            
        Returns:
            Dictionary with improvement metrics
        """
        orig_n = original.nutrition_facts
        sub_n = substitute.nutrition_facts
        
        # Normalize to same serving size (original's serving size)
        scale = orig_n.serving_size_grams / (sub_n.serving_size_grams or orig_n.serving_size_grams)
        
        # Calculate percentage changes
        changes = {
            'sugar_reduction_percent': ((orig_n.sugars_g - sub_n.sugars_g * scale) / 
                                       max(orig_n.sugars_g, 0.1)) * 100 if orig_n.sugars_g > 0 else 0,
            'sodium_reduction_percent': ((orig_n.sodium_mg - sub_n.sodium_mg * scale) / 
                                        max(orig_n.sodium_mg, 1)) * 100 if orig_n.sodium_mg > 0 else 0,
            'calorie_reduction_percent': ((orig_n.calories - sub_n.calories * scale) / 
                                         max(orig_n.calories, 1)) * 100 if orig_n.calories > 0 else 0,
            'fiber_increase_percent': ((sub_n.dietary_fiber_g * scale - orig_n.dietary_fiber_g) / 
                                      max(orig_n.dietary_fiber_g, 0.1)) * 100 if orig_n.dietary_fiber_g > 0 else 0,
        }
        
        # Health improvement score (0-100)
        improvement_score = (
            max(0, changes['sugar_reduction_percent']) * 0.35 +
            max(0, changes['sodium_reduction_percent']) * 0.35 +
            max(0, changes['calorie_reduction_percent']) * 0.15 +
            max(0, changes['fiber_increase_percent']) * 0.15
        ) / 100 * 100
        
        return {
            **changes,
            'improvement_score': round(improvement_score, 1),
        }


class SubstitutionRecommendationEngine:
    """Main engine for generating food substitution recommendations"""
    
    def __init__(self, food_database: Optional[List[FoodItem]] = None):
        self.matcher = NutrientSimilarityMatcher()
        self.food_database = food_database or []
    
    def add_to_database(self, food_item: FoodItem):
        """Add a food item to the substitution database"""
        self.food_database.append(food_item)
    
    def find_substitutes(self, original_food: FoodItem, 
                        user_profile: Optional[UserProfile] = None,
                        max_suggestions: int = 5,
                        min_similarity: float = 0.4) -> SubstitutionRecommendation:
        """
        Find healthier substitutes for a food item
        
        Args:
            original_food: Food item to replace
            user_profile: Optional user profile for personalization
            max_suggestions: Maximum number of substitutes to return
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            SubstitutionRecommendation with ranked alternatives
        """
        recommendation = SubstitutionRecommendation(
            original_item_id=original_food.item_id,
            substitute_items=[]
        )
        
        candidates = []
        
        for candidate in self.food_database:
            # Skip the original food
            if candidate.item_id == original_food.item_id:
                continue
            
            # Skip if classification is worse
            if candidate.classification.value.lower() in ['avoid', 'moderate']:
                if original_food.classification.value.lower() == 'suitable':
                    continue
            
            # Calculate similarity
            similarity = self.matcher.calculate_similarity(original_food, candidate)
            
            if similarity < min_similarity:
                continue
            
            # Calculate health improvement
            improvement = self.matcher.calculate_health_improvement(
                original_food, candidate, user_profile
            )
            
            # Skip if substitute is not healthier
            if improvement['improvement_score'] < 10:
                continue
            
            candidates.append({
                'food': candidate,
                'similarity': similarity,
                'improvement': improvement,
            })
        
        # Sort by improvement score * similarity (weighted by personalization)
        def score_substitute(c):
            base_score = c['improvement']['improvement_score'] * 0.7 + c['similarity'] * 100 * 0.3
            
            # Personalize based on user profile
            if user_profile and user_profile.has_diabetes:
                # Prioritize sugar reduction
                base_score += c['improvement']['sugar_reduction_percent'] * 0.1
            
            if user_profile and user_profile.hypertension_severity.value != 'normal':
                # Prioritize sodium reduction
                base_score += c['improvement']['sodium_reduction_percent'] * 0.1
            
            return base_score
        
        candidates.sort(key=score_substitute, reverse=True)
        
        # Select top N
        recommendation.substitute_items = [c['food'] for c in candidates[:max_suggestions]]
        
        # Calculate overall metrics
        if recommendation.substitute_items:
            best_improvement = candidates[0]['improvement']
            recommendation.sugar_reduction_percent = round(best_improvement['sugar_reduction_percent'], 1)
            recommendation.sodium_reduction_percent = round(best_improvement['sodium_reduction_percent'], 1)
            recommendation.calorie_reduction_percent = round(best_improvement['calorie_reduction_percent'], 1)
            
            recommendation.reasoning = self._generate_substitution_reasoning(
                original_food, recommendation, best_improvement, user_profile
            )
        
        return recommendation
    
    def _generate_substitution_reasoning(self, original: FoodItem, 
                                        recommendation: SubstitutionRecommendation,
                                        best_improvement: Dict,
                                        user_profile: Optional[UserProfile]) -> str:
        """Generate medical reasoning for substitution"""
        
        reasoning = f"Substitution Recommendations for {original.name}\n\n"
        
        reasoning += "Why switch:\n"
        
        if best_improvement['sugar_reduction_percent'] > 10:
            reasoning += f"  • Reduces sugar by ~{best_improvement['sugar_reduction_percent']:.0f}%\n"
        
        if best_improvement['sodium_reduction_percent'] > 10:
            reasoning += f"  • Reduces sodium by ~{best_improvement['sodium_reduction_percent']:.0f}%\n"
        
        if best_improvement['calorie_reduction_percent'] > 10:
            reasoning += f"  • Reduces calories by ~{best_improvement['calorie_reduction_percent']:.0f}%\n"
        
        if best_improvement['fiber_increase_percent'] > 10:
            reasoning += f"  • Increases fiber by ~{best_improvement['fiber_increase_percent']:.0f}%\n"
        
        if recommendation.substitute_items:
            reasoning += f"\nTop recommendation: {recommendation.substitute_items[0].name}\n"
            reasoning += f"  Brand: {recommendation.substitute_items[0].brand}\n"
            reasoning += f"  Classification: {recommendation.substitute_items[0].classification.value}\n"
        
        if user_profile and user_profile.has_diabetes:
            reasoning += "\n💉 For your diabetes management:\n"
            if recommendation.substitute_items:
                best_sub = recommendation.substitute_items[0]
                if best_sub.clinical_metrics.glycemic_load:
                    reasoning += f"  • Lower glycemic load: {best_sub.clinical_metrics.glycemic_load:.1f}\n"
        
        if user_profile and user_profile.hypertension_severity.value != 'normal':
            reasoning += "\n🫀 For your hypertension management:\n"
            if recommendation.substitute_items:
                best_sub = recommendation.substitute_items[0]
                reasoning += f"  • Lower sodium content: {best_sub.nutrition_facts.sodium_mg:.0f}mg\n"
        
        return reasoning
    
    def batch_find_substitutes(self, foods: List[FoodItem], 
                              user_profile: Optional[UserProfile] = None) -> Dict[str, SubstitutionRecommendation]:
        """
        Find substitutes for multiple foods
        
        Args:
            foods: List of food items
            user_profile: Optional user profile
            
        Returns:
            Dictionary mapping food IDs to recommendations
        """
        recommendations = {}
        for food in foods:
            recommendations[food.item_id] = self.find_substitutes(food, user_profile)
        
        return recommendations
