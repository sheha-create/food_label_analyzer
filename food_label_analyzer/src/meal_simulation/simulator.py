"""
Meal Simulation Module
Evaluates multi-food consumption impact and meal planning
"""
from typing import List, Dict, Optional
from dataclasses import field
from datetime import datetime
try:
    from food_label_analyzer.src.config import (
        FoodItem, MealSimulationResult, UserProfile, FoodClassification,
        MEDICAL_THRESHOLDS, GI_RANGES, SODIUM_ALERTS, SUGAR_ALERTS,
    )
except ImportError:
    from src.config import (
        FoodItem, MealSimulationResult, UserProfile, FoodClassification,
        MEDICAL_THRESHOLDS, GI_RANGES, SODIUM_ALERTS, SUGAR_ALERTS,
    )


class MealSimulator:
    """Simulates and evaluates multi-food meals"""
    
    def __init__(self, user_profile: Optional[UserProfile] = None):
        self.user_profile = user_profile
    
    def simulate_meal(self, foods: List[FoodItem], 
                     meal_name: str = "Custom Meal",
                     user_profile: Optional[UserProfile] = None) -> MealSimulationResult:
        """
        Simulate and evaluate a meal composed of multiple foods
        
        Args:
            foods: List of FoodItem objects in the meal
            meal_name: Name of the meal
            user_profile: Optional user profile for personalized analysis
            
        Returns:
            MealSimulationResult with aggregated metrics and assessment
        """
        profile = user_profile or self.user_profile
        
        meal = MealSimulationResult(
            meal_id=f"meal_{datetime.now().timestamp()}",
            foods=foods,
        )
        
        # Aggregate nutrition from all foods
        for food in foods:
            n = food.nutrition_facts
            meal.total_calories += n.calories
            meal.total_carbs_g += n.total_carbs_g
            meal.total_sugars_g += n.sugars_g
            meal.total_sodium_mg += n.sodium_mg
            meal.total_fiber_g += n.dietary_fiber_g
            meal.total_protein_g += n.protein_g
        
        # Calculate estimated glycemic load
        meal.estimated_glycemic_load = self._calculate_meal_glycemic_load(foods)
        
        # Calculate sodium load percentage
        daily_sodium_allowance = (profile.max_daily_sodium_mg if profile 
                                 else MEDICAL_THRESHOLDS['daily_sodium_mg'])
        meal.sodium_load_percentage = (meal.total_sodium_mg / daily_sodium_allowance * 100) if daily_sodium_allowance > 0 else 0
        
        # Determine meal classification
        meal.meal_safety_score = self._calculate_safety_score(meal, profile)
        meal.meal_classification = self._classify_meal(meal, meal.meal_safety_score, profile)
        
        # Generate recommendations
        meal.recommendations = self._generate_meal_recommendations(meal, foods, profile)
        
        return meal
    
    def _calculate_meal_glycemic_load(self, foods: List[FoodItem]) -> float:
        """Calculate total glycemic load of the meal"""
        total_gl = 0.0
        
        for food in foods:
            if food.clinical_metrics.glycemic_load:
                total_gl += food.clinical_metrics.glycemic_load
        
        return round(total_gl, 1)
    
    def _calculate_safety_score(self, meal: MealSimulationResult, 
                               profile: Optional[UserProfile]) -> float:
        """
        Calculate meal safety score (0-100)
        
        Args:
            meal: MealSimulationResult
            profile: Optional user profile
            
        Returns:
            Safety score 0-100
        """
        score = 100.0
        
        # Check against diabetes thresholds
        if profile and profile.has_diabetes:
            # High sugar penalty
            daily_sugar_allowance = profile.max_daily_sugar_g or MEDICAL_THRESHOLDS['daily_sugar_grams']
            if meal.total_sugars_g > daily_sugar_allowance * 0.5:  # More than half daily allowance
                score -= min(30, (meal.total_sugars_g / daily_sugar_allowance) * 30)
            
            # High GL penalty
            if meal.estimated_glycemic_load > 50:
                score -= min(20, (meal.estimated_glycemic_load / 100) * 20)
        
        # Check against hypertension thresholds
        if profile and profile.hypertension_severity.value != 'normal':
            daily_sodium_allowance = profile.max_daily_sodium_mg or MEDICAL_THRESHOLDS['daily_sodium_mg']
            if meal.total_sodium_mg > daily_sodium_allowance * 0.5:
                score -= min(25, (meal.total_sodium_mg / daily_sodium_allowance) * 25)
        
        # General nutrition checks
        # Low fiber penalty
        if meal.total_fiber_g < 3:
            score -= 10
        else:
            score += 5  # Bonus for good fiber
        
        # Carb to fiber ratio check
        if meal.total_carbs_g > 0:
            carb_fiber_ratio = meal.total_carbs_g / (meal.total_fiber_g + 0.1)
            if carb_fiber_ratio > 15:
                score -= 10
        
        # High sodium penalty (general)
        if meal.total_sodium_mg > SODIUM_ALERTS['high'] * 3:
            score -= 10
        
        score = max(0, min(100, score))
        return round(score, 1)
    
    def _classify_meal(self, meal: MealSimulationResult, safety_score: float,
                      profile: Optional[UserProfile]) -> FoodClassification:
        """Classify meal as suitable, moderate, or avoid"""
        
        if safety_score >= 75:
            return FoodClassification.SUITABLE
        elif safety_score >= 50:
            return FoodClassification.MODERATE
        else:
            return FoodClassification.AVOID
    
    def _generate_meal_recommendations(self, meal: MealSimulationResult,
                                      foods: List[FoodItem],
                                      profile: Optional[UserProfile]) -> List[str]:
        """Generate personalized meal recommendations"""
        
        recommendations = []
        
        # Diabetes-specific recommendations
        if profile and profile.has_diabetes:
            daily_carb_allowance = profile.carb_tolerance_g or 45  # Per meal default
            daily_sugar_allowance = profile.max_daily_sugar_g or MEDICAL_THRESHOLDS['daily_sugar_grams']
            
            if meal.total_carbs_g > daily_carb_allowance * 1.25:
                recommendations.append(f"⚠️  High carbohydrate meal ({meal.total_carbs_g:.0f}g). Aim for <{daily_carb_allowance}g per meal.")
            
            if meal.total_sugars_g > daily_sugar_allowance * 0.3:
                recommendations.append(f"⚠️  High sugar content ({meal.total_sugars_g:.1f}g). Consider lower-sugar alternatives.")
            
            if meal.estimated_glycemic_load > 30:
                recommendations.append(f"💊 High glycemic load ({meal.estimated_glycemic_load:.0f}). Pair with protein or fat for better glucose control.")
            
            if meal.total_fiber_g >= 5:
                recommendations.append("✓ Good fiber content. Helps moderate blood sugar rise.")
        
        # Hypertension-specific recommendations
        if profile and profile.hypertension_severity.value != 'normal':
            daily_sodium = profile.max_daily_sodium_mg or MEDICAL_THRESHOLDS['daily_sodium_mg']
            
            if meal.total_sodium_mg > daily_sodium * 0.4:
                recommendations.append(f"🫀 High sodium meal ({meal.total_sodium_mg:.0f}mg). Aim for <{daily_sodium * 0.4:.0f}mg to manage blood pressure.")
        
        # General recommendations
        if meal.total_protein_g < 10:
            recommendations.append("Add protein source (chicken, fish, legumes, dairy) to improve satiety.")
        
        if meal.total_fiber_g < 3:
            recommendations.append("Low fiber content. Add vegetables, fruits, or whole grains.")
        
        # Caloric recommendations
        if profile:
            daily_calories = profile.max_daily_calories or MEDICAL_THRESHOLDS['daily_calories']
            if meal.total_calories > daily_calories * 0.4:
                recommendations.append(f"Calorie-dense meal ({meal.total_calories:.0f}cal). Consider portion reduction.")
        
        # Limit recommendations to top 4
        return recommendations[:4]
    
    def simulate_daily_consumption(self, meals: List[MealSimulationResult],
                                   user_profile: Optional[UserProfile] = None) -> Dict:
        """
        Simulate and evaluate full day consumption from multiple meals
        
        Args:
            meals: List of MealSimulationResult objects
            user_profile: Optional user profile
            
        Returns:
            Dictionary with daily accumulation metrics
        """
        profile = user_profile or self.user_profile
        
        daily_totals = {
            'total_calories': 0.0,
            'total_carbs_g': 0.0,
            'total_sugars_g': 0.0,
            'total_sodium_mg': 0.0,
            'total_fiber_g': 0.0,
            'total_protein_g': 0.0,
            'total_gl': 0.0,
            'meal_count': len(meals),
        }
        
        for meal in meals:
            daily_totals['total_calories'] += meal.total_calories
            daily_totals['total_carbs_g'] += meal.total_carbs_g
            daily_totals['total_sugars_g'] += meal.total_sugars_g
            daily_totals['total_sodium_mg'] += meal.total_sodium_mg
            daily_totals['total_fiber_g'] += meal.total_fiber_g
            daily_totals['total_protein_g'] += meal.total_protein_g
            daily_totals['total_gl'] += meal.estimated_glycemic_load
        
        # Calculate compliance percentages
        daily_thresholds = {
            'calories': profile.max_daily_calories if profile else MEDICAL_THRESHOLDS['daily_calories'],
            'sugar': profile.max_daily_sugar_g if profile else MEDICAL_THRESHOLDS['daily_sugar_grams'],
            'sodium': profile.max_daily_sodium_mg if profile else MEDICAL_THRESHOLDS['daily_sodium_mg'],
            'carbs': profile.carb_tolerance_g * 5 if profile else 225,  # Default 45g/meal * 5 meals
        }
        
        compliance = {
            'calories_percent': (daily_totals['total_calories'] / daily_thresholds['calories'] * 100) if daily_thresholds['calories'] > 0 else 0,
            'sugar_percent': (daily_totals['total_sugars_g'] / daily_thresholds['sugar'] * 100) if daily_thresholds['sugar'] > 0 else 0,
            'sodium_percent': (daily_totals['total_sodium_mg'] / daily_thresholds['sodium'] * 100) if daily_thresholds['sodium'] > 0 else 0,
            'carbs_percent': (daily_totals['total_carbs_g'] / daily_thresholds['carbs'] * 100) if daily_thresholds['carbs'] > 0 else 0,
        }
        
        # Determine daily compliance status
        compliant_metrics = sum([1 for v in compliance.values() if v <= 100])
        daily_compliance_score = (compliant_metrics / len(compliance)) * 100
        
        daily_totals['thresholds'] = daily_thresholds
        daily_totals['compliance'] = compliance
        daily_totals['daily_compliance_score'] = round(daily_compliance_score, 1)
        
        # Generate daily summary
        daily_totals['summary'] = self._generate_daily_summary(daily_totals, compliance, profile)
        
        return daily_totals
    
    def _generate_daily_summary(self, daily_totals: Dict, compliance: Dict,
                               profile: Optional[UserProfile]) -> str:
        """Generate daily consumption summary"""
        
        summary = "Daily Consumption Summary\n"
        summary += "=" * 50 + "\n\n"
        
        summary += "Totals:\n"
        summary += f"  Meals: {daily_totals['meal_count']}\n"
        summary += f"  Calories: {daily_totals['total_calories']:.0f}\n"
        summary += f"  Carbs: {daily_totals['total_carbs_g']:.1f}g | Sugar: {daily_totals['total_sugars_g']:.1f}g | Fiber: {daily_totals['total_fiber_g']:.1f}g\n"
        summary += f"  Sodium: {daily_totals['total_sodium_mg']:.0f}mg\n"
        summary += f"  Protein: {daily_totals['total_protein_g']:.1f}g\n\n"
        
        summary += "Compliance Status:\n"
        
        # Color-coded compliance
        for metric, percent in compliance.items():
            status = "✓" if percent <= 100 else "✗"
            summary += f"  {status} {metric.replace('_', ' ').title()}: {percent:.0f}%\n"
        
        # Overall assessment
        overall_score = daily_totals['daily_compliance_score']
        if overall_score >= 80:
            assessment = "👍 EXCELLENT - All metrics within healthy ranges"
        elif overall_score >= 60:
            assessment = "⚠️  GOOD - Most metrics on track"
        elif overall_score >= 40:
            assessment = "⚠️  FAIR - Some metrics need attention"
        else:
            assessment = "❌ POOR - Multiple metrics exceed recommendations"
        
        summary += f"\nOverall Assessment: {assessment}\n"
        
        if profile and profile.has_diabetes:
            summary += f"\nDiabetes Note: Total glycemic load = {daily_totals['total_gl']:.0f}\n"
            if daily_totals['total_gl'] <= 100:
                summary += "  ✓ GL within recommended range"
            else:
                summary += f"  ⚠️  GL exceeds typical range by {daily_totals['total_gl'] - 100:.0f} points"
        
        return summary
