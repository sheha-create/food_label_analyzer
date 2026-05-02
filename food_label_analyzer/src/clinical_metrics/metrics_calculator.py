"""
Clinical Metrics Computation Module
Calculates glycemic index, glycemic load, sodium load, and other medical metrics
"""
from typing import Optional, Dict
import numpy as np
from dataclasses import dataclass
try:
    from food_label_analyzer.src.config import (
        NutritionFacts, ClinicalMetrics, UserProfile,
        MEDICAL_THRESHOLDS, GI_RANGES, SODIUM_ALERTS, SUGAR_ALERTS
    )
except ImportError:
    from src.config import (
        NutritionFacts, ClinicalMetrics, UserProfile,
        MEDICAL_THRESHOLDS, GI_RANGES, SODIUM_ALERTS, SUGAR_ALERTS
    )


class GlycemicIndexCalculator:
    """Calculate glycemic index (GI) for foods"""
    
    # Pre-computed GI values for common foods (extensible database)
    GI_DATABASE = {
        # Grains and cereals
        'white bread': 75, 'whole wheat bread': 51, 'oatmeal': 55,
        'brown rice': 60, 'white rice': 73, 'pasta': 46,
        
        # Fruits
        'watermelon': 76, 'pineapple': 66, 'mango': 51,
        'banana': 62, 'orange': 40, 'apple': 36,
        'grapes': 46, 'berries': 32,
        
        # Vegetables
        'potato': 78, 'sweet potato': 63, 'carrot': 35,
        'broccoli': 15, 'spinach': 15, 'green beans': 30,
        
        # Legumes
        'lentils': 21, 'chickpeas': 28, 'kidney beans': 23,
        'peanuts': 13,
        
        # Dairy
        'milk': 32, 'yogurt': 36, 'ice cream': 51,
        
        # Sweets and snacks
        'chocolate': 43, 'cookies': 69, 'chips': 56,
    }
    
    def __init__(self):
        self.gi_values_used = []
    
    def estimate_gi(self, food_name: str, carbs_g: float, 
                   fiber_g: float = 0.0) -> Optional[float]:
        """
        Estimate glycemic index for a food item
        
        Args:
            food_name: Name of the food
            carbs_g: Total carbohydrates in grams
            fiber_g: Dietary fiber in grams
            
        Returns:
            Estimated GI value (0-100) or None if cannot estimate
        """
        # Lookup in database
        food_lower = food_name.lower()
        for db_food, gi_value in self.GI_DATABASE.items():
            if db_food in food_lower:
                # Adjust GI based on fiber content (high fiber lowers GI)
                if fiber_g > 0:
                    fiber_adjustment = min(10, fiber_g * 2)  # Up to 10 point reduction
                    adjusted_gi = max(15, gi_value - fiber_adjustment)
                else:
                    adjusted_gi = gi_value
                
                self.gi_values_used.append({'food': food_name, 'gi': adjusted_gi})
                return adjusted_gi
        
        # Default estimation based on carbs and fiber
        if carbs_g > 0:
            # Simple heuristic: high carbs with low fiber = higher GI
            carb_to_fiber_ratio = carbs_g / (fiber_g + 1)  # +1 to avoid division by zero
            
            if carb_to_fiber_ratio > 10:
                default_gi = 70  # High GI
            elif carb_to_fiber_ratio > 5:
                default_gi = 55  # Medium GI
            else:
                default_gi = 35  # Low GI
            
            self.gi_values_used.append({'food': food_name, 'gi': default_gi, 'estimated': True})
            return default_gi
        
        return None
    
    def get_gi_classification(self, gi_value: float) -> str:
        """Classify GI value"""
        if gi_value < GI_RANGES['low'][1]:
            return 'Low GI'
        elif gi_value < GI_RANGES['medium'][1]:
            return 'Medium GI'
        else:
            return 'High GI'


class GlycemicLoadCalculator:
    """Calculate glycemic load (GL) for foods and meals"""
    
    def calculate_gl(self, gi_value: float, carbs_g: float, 
                    serving_size_g: float = 100) -> float:
        """
        Calculate glycemic load per serving
        
        GL = (GI × Carbs in grams) / 100
        
        Args:
            gi_value: Glycemic index (0-100)
            carbs_g: Available carbohydrates (total carbs - fiber) in grams
            serving_size_g: Serving size in grams
            
        Returns:
            Glycemic load value
        """
        if gi_value is None or carbs_g is None:
            return 0.0
        
        # Use available carbs (total carbs - fiber)
        available_carbs = carbs_g
        
        gl = (gi_value * available_carbs) / 100.0
        
        return round(gl, 1)
    
    def classify_gl(self, gl_value: float) -> str:
        """
        Classify GL value
        GL < 10: Low
        GL 10-20: Medium
        GL > 20: High
        """
        if gl_value < 10:
            return 'Low GL'
        elif gl_value < 20:
            return 'Medium GL'
        else:
            return 'High GL'
    
    def calculate_daily_meal_gl(self, meals: list) -> float:
        """Calculate total GL for daily meals"""
        return sum([meal.get('gl', 0) for meal in meals])


class SodiumLoadCalculator:
    """Calculate sodium load and daily allowance accumulation"""
    
    def __init__(self, daily_allowance_mg: float = MEDICAL_THRESHOLDS['daily_sodium_mg']):
        self.daily_allowance_mg = daily_allowance_mg
    
    def calculate_sodium_load_percentage(self, sodium_mg: float) -> float:
        """
        Calculate percentage of daily sodium allowance
        
        Args:
            sodium_mg: Sodium in milligrams
            
        Returns:
            Percentage of daily allowance
        """
        if self.daily_allowance_mg == 0:
            return 0.0
        
        percentage = (sodium_mg / self.daily_allowance_mg) * 100
        return round(percentage, 1)
    
    def classify_sodium(self, sodium_mg: float) -> str:
        """Classify sodium content per serving"""
        if sodium_mg >= SODIUM_ALERTS['high']:
            return 'High Sodium'
        elif sodium_mg >= SODIUM_ALERTS['medium']:
            return 'Moderate Sodium'
        else:
            return 'Low Sodium'
    
    def check_daily_accumulation(self, daily_items: list, 
                                allowance_override_mg: Optional[float] = None) -> Dict:
        """
        Check daily sodium accumulation
        
        Args:
            daily_items: List of items consumed during the day
            allowance_override_mg: Override daily allowance
            
        Returns:
            Dictionary with accumulation analysis
        """
        daily_allowance = allowance_override_mg or self.daily_allowance_mg
        total_sodium = sum([item.get('sodium_mg', 0) for item in daily_items])
        
        exceeded = total_sodium > daily_allowance
        excess_mg = max(0, total_sodium - daily_allowance)
        
        return {
            'total_sodium_mg': total_sodium,
            'daily_allowance_mg': daily_allowance,
            'percentage_of_allowance': (total_sodium / daily_allowance * 100) if daily_allowance > 0 else 0,
            'exceeded': exceeded,
            'excess_mg': excess_mg,
            'remaining_mg': max(0, daily_allowance - total_sodium),
        }


class SugarLoadCalculator:
    """Calculate sugar load and daily accumulation"""
    
    def __init__(self, daily_allowance_g: float = MEDICAL_THRESHOLDS['daily_sugar_grams']):
        self.daily_allowance_g = daily_allowance_g
    
    def calculate_sugar_load_percentage(self, sugar_g: float) -> float:
        """
        Calculate percentage of daily sugar allowance
        
        Args:
            sugar_g: Sugar in grams
            
        Returns:
            Percentage of daily allowance
        """
        if self.daily_allowance_g == 0:
            return 0.0
        
        percentage = (sugar_g / self.daily_allowance_g) * 100
        return round(percentage, 1)
    
    def classify_sugar(self, sugar_g: float) -> str:
        """Classify sugar content per serving"""
        if sugar_g >= SUGAR_ALERTS['high']:
            return 'High Sugar'
        elif sugar_g >= SUGAR_ALERTS['medium']:
            return 'Moderate Sugar'
        else:
            return 'Low Sugar'
    
    def detect_hidden_sugars(self, sugars_g: float, added_sugars_g: Optional[float],
                            sugar_alcohols_g: Optional[float]) -> Dict:
        """
        Detect and quantify hidden sugars
        
        Args:
            sugars_g: Total sugars
            added_sugars_g: Declared added sugars
            sugar_alcohols_g: Sugar alcohols
            
        Returns:
            Dictionary with hidden sugar analysis
        """
        hidden_sugars = 0.0
        sources = []
        
        # If total sugars > added sugars + sugar alcohols, there's hidden content
        total_declared = (added_sugars_g or 0) + (sugar_alcohols_g or 0)
        hidden_sugars = max(0, sugars_g - total_declared)
        
        if hidden_sugars > 0:
            sources.append(f"Undeclared sugars: {hidden_sugars:.1f}g (from natural/fruit sources)")
        
        return {
            'total_sugars_g': sugars_g,
            'declared_added_sugars_g': added_sugars_g or 0,
            'sugar_alcohols_g': sugar_alcohols_g or 0,
            'hidden_sugars_g': hidden_sugars,
            'sources': sources,
            'warning': hidden_sugars > self.daily_allowance_g * 0.25,
        }


class ClinicalMetricsComputer:
    """Main class to compute all clinical metrics"""
    
    def __init__(self, user_profile: Optional[UserProfile] = None):
        self.user_profile = user_profile
        self.gi_calculator = GlycemicIndexCalculator()
        self.gl_calculator = GlycemicLoadCalculator()
        self.sodium_calculator = SodiumLoadCalculator()
        self.sugar_calculator = SugarLoadCalculator()
    
    def compute_metrics(self, nutrition_facts: NutritionFacts, 
                       food_name: str, 
                       user_profile: Optional[UserProfile] = None) -> ClinicalMetrics:
        """
        Compute all clinical metrics for a food item
        
        Args:
            nutrition_facts: NutritionFacts object
            food_name: Name of the food for GI lookup
            user_profile: Optional user profile for personalized thresholds
            
        Returns:
            ClinicalMetrics object
        """
        profile = user_profile or self.user_profile
        
        metrics = ClinicalMetrics()
        
        # Calculate glycemic metrics
        available_carbs = nutrition_facts.total_carbs_g - nutrition_facts.dietary_fiber_g
        gi = self.gi_calculator.estimate_gi(food_name, nutrition_facts.total_carbs_g,
                                           nutrition_facts.dietary_fiber_g)
        metrics.glycemic_index = gi
        
        if gi is not None:
            metrics.glycemic_load = self.gl_calculator.calculate_gl(
                gi, available_carbs, nutrition_facts.serving_size_grams
            )
        
        # Calculate sodium metrics
        metrics.sodium_load_percentage = self.sodium_calculator.calculate_sodium_load_percentage(
            nutrition_facts.sodium_mg
        )
        
        # Calculate sugar metrics
        metrics.sugar_load_percentage = self.sugar_calculator.calculate_sugar_load_percentage(
            nutrition_facts.sugars_g
        )
        
        # Calculate caloric percentage
        daily_calories = profile.max_daily_calories if profile else MEDICAL_THRESHOLDS['daily_calories']
        metrics.caloric_percentage = (nutrition_facts.calories / daily_calories * 100) if daily_calories > 0 else 0
        
        # Calculate macronutrient ratios
        if nutrition_facts.total_carbs_g > 0:
            metrics.carb_to_fiber_ratio = nutrition_facts.total_carbs_g / (
                nutrition_facts.dietary_fiber_g + 0.1
            )
        
        # Sugar density
        if nutrition_facts.calories > 0:
            metrics.sugar_per_100cal = (nutrition_facts.sugars_g * 100) / nutrition_facts.calories
            metrics.sodium_per_100cal = (nutrition_facts.sodium_mg * 100) / nutrition_facts.calories
        
        # Generate nutrient density score (0-100, higher is better)
        metrics.nutrient_density_score = self._calculate_nutrient_density_score(nutrition_facts)
        
        # Generate reasoning text
        metrics.reasoning_text = self._generate_reasoning(nutrition_facts, metrics, food_name, profile)
        
        # Identify risk factors
        metrics.risk_factors = self._identify_risk_factors(nutrition_facts, metrics, profile)
        
        return metrics
    
    def _calculate_nutrient_density_score(self, nutrition: NutritionFacts) -> float:
        """
        Calculate nutrient density score (0-100)
        Considers fiber, protein, and micronutrients relative to calories
        """
        if nutrition.calories == 0:
            return 0.0
        
        score = 0.0
        
        # Fiber score (higher is better)
        fiber_score = min(30, (nutrition.dietary_fiber_g / nutrition.serving_size_grams) * 1000)
        score += fiber_score
        
        # Protein score
        protein_score = min(30, (nutrition.protein_g / nutrition.serving_size_grams) * 1000)
        score += protein_score
        
        # Saturation score (lower saturated fat is better)
        saturation_penalty = min(20, (nutrition.saturated_fat_g / nutrition.total_fat_g * 20) 
                               if nutrition.total_fat_g > 0 else 0)
        score += (20 - saturation_penalty)
        
        # Sugar penalty (lower is better)
        sugar_penalty = min(20, (nutrition.sugars_g / nutrition.total_carbs_g * 20) 
                           if nutrition.total_carbs_g > 0 else 0)
        score += (20 - sugar_penalty)
        
        return round(min(100, max(0, score)), 1)
    
    def _generate_reasoning(self, nutrition: NutritionFacts, metrics: ClinicalMetrics,
                           food_name: str, profile: Optional[UserProfile]) -> str:
        """Generate medical reasoning for the metrics"""
        reasoning = f"Food: {food_name}\n"
        
        # GI/GL reasoning
        if metrics.glycemic_index:
            gi_class = self.gi_calculator.get_gi_classification(metrics.glycemic_index)
            reasoning += f"\n• Glycemic Index: {metrics.glycemic_index:.0f} ({gi_class})"
            if metrics.glycemic_load:
                gl_class = self.gl_calculator.classify_gl(metrics.glycemic_load)
                reasoning += f"\n  Glycemic Load: {metrics.glycemic_load:.1f} ({gl_class})"
        
        # Sodium reasoning
        sodium_class = self.sodium_calculator.classify_sodium(nutrition.sodium_mg)
        reasoning += f"\n• Sodium: {nutrition.sodium_mg:.0f}mg ({sodium_class}) - {metrics.sodium_load_percentage:.1f}% of daily allowance"
        
        # Sugar reasoning
        hidden_sugar_info = self.sugar_calculator.detect_hidden_sugars(
            nutrition.sugars_g, nutrition.added_sugars_g, nutrition.sugar_alcohols_g
        )
        sugar_class = self.sugar_calculator.classify_sugar(nutrition.sugars_g)
        reasoning += f"\n• Sugars: {nutrition.sugars_g:.1f}g ({sugar_class})"
        if hidden_sugar_info['hidden_sugars_g'] > 0:
            reasoning += f"\n  Hidden sugars: {hidden_sugar_info['hidden_sugars_g']:.1f}g"
        
        # Fiber reasoning
        if profile and profile.has_diabetes:
            reasoning += f"\n• Dietary Fiber: {nutrition.dietary_fiber_g:.1f}g (helps manage blood sugar)"
        
        # Personalization for diabetes
        if profile and profile.has_diabetes:
            daily_carb_tolerance = profile.carb_tolerance_g or 45  # Default serving
            reasoning += f"\n• For your diabetes profile: serving provides {nutrition.total_carbs_g:.1f}g carbs"
        
        return reasoning
    
    def _identify_risk_factors(self, nutrition: NutritionFacts, metrics: ClinicalMetrics,
                             profile: Optional[UserProfile]) -> list:
        """Identify health risk factors"""
        risk_factors = []
        
        # High sodium risk
        if nutrition.sodium_mg > SODIUM_ALERTS['high']:
            risk_factors.append(f"High sodium ({nutrition.sodium_mg:.0f}mg) - risk for hypertension")
        
        # High sugar risk
        if nutrition.sugars_g > SUGAR_ALERTS['high']:
            risk_factors.append(f"High sugar content ({nutrition.sugars_g:.1f}g)")
        
        # High GI risk
        if metrics.glycemic_index and metrics.glycemic_index > GI_RANGES['high'][0]:
            risk_factors.append(f"High glycemic index ({metrics.glycemic_index:.0f}) - rapid blood sugar spike")
        
        # Low fiber relative to carbs
        if metrics.carb_to_fiber_ratio > 10:
            risk_factors.append("Low fiber content relative to carbohydrates")
        
        # High caloric density
        if nutrition.calories > 250:
            risk_factors.append("High caloric density per serving")
        
        # Trans fat risk
        if nutrition.trans_fat_g > 0:
            risk_factors.append("Contains trans fats - cardiovascular risk")
        
        return risk_factors
