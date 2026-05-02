"""
Fraud Detection Module
Identifies deceptive serving sizes, unrealistic nutrition claims, and food fraud
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import field
try:
    from food_label_analyzer.src.config import (
        NutritionFacts, IngredientsList, FraudDetectionResult, FoodItem,
    )
except ImportError:
    from src.config import (
        NutritionFacts, IngredientsList, FraudDetectionResult, FoodItem,
    )


class NutritionMarketDatabase:
    """Database of market ranges for common foods"""
    
    # Food category -> nutrition ranges (per 100g serving)
    MARKET_RANGES = {
        'cookies': {
            'calories_range': (400, 550),
            'sugar_range': (20, 35),
            'fiber_range': (1, 4),
            'sodium_range': (100, 400),
        },
        'bread': {
            'calories_range': (200, 300),
            'sugar_range': (2, 8),
            'fiber_range': (3, 8),
            'sodium_range': (300, 600),
        },
        'cereal': {
            'calories_range': (300, 450),
            'sugar_range': (0, 15),
            'fiber_range': (2, 12),
            'sodium_range': (100, 400),
        },
        'juice': {
            'calories_range': (35, 60),
            'sugar_range': (8, 13),
            'fiber_range': (0, 1),
            'sodium_range': (0, 50),
        },
        'yogurt': {
            'calories_range': (40, 100),
            'sugar_range': (3, 8),
            'fiber_range': (0, 2),
            'sodium_range': (40, 150),
        },
        'snack_bar': {
            'calories_range': (150, 250),
            'sugar_range': (5, 15),
            'fiber_range': (2, 10),
            'sodium_range': (100, 300),
        },
        'chips': {
            'calories_range': (450, 560),
            'sugar_range': (0, 2),
            'fiber_range': (1, 4),
            'sodium_range': (300, 600),
        },
        'chocolate': {
            'calories_range': (450, 550),
            'sugar_range': (45, 65),
            'fiber_range': (2, 8),
            'sodium_range': (50, 150),
        },
    }
    
    def get_market_range(self, category: str) -> Optional[Dict]:
        """Get market nutrition range for a food category"""
        return self.MARKET_RANGES.get(category.lower())
    
    def is_realistic(self, nutrition: NutritionFacts, category: str) -> Tuple[bool, List[str]]:
        """
        Check if nutrition facts are realistic compared to market ranges
        
        Args:
            nutrition: NutritionFacts to check
            category: Food category
            
        Returns:
            Tuple of (is_realistic, list_of_concerns)
        """
        market_range = self.get_market_range(category)
        if not market_range:
            return True, []  # No data, assume realistic
        
        concerns = []
        
        # Normalize to per 100g for comparison
        serving_size = nutrition.serving_size_grams or 100
        scale_factor = 100 / serving_size if serving_size > 0 else 1
        
        calories_per_100g = nutrition.calories * scale_factor
        sugar_per_100g = nutrition.sugars_g * scale_factor
        fiber_per_100g = nutrition.dietary_fiber_g * scale_factor
        sodium_per_100g = nutrition.sodium_mg * scale_factor
        
        # Check each nutrient
        if 'calories_range' in market_range:
            cal_range = market_range['calories_range']
            if not (cal_range[0] * 0.5 <= calories_per_100g <= cal_range[1] * 2):
                concerns.append(f"Calorie content ({calories_per_100g:.0f}/100g) outside typical range ({cal_range})")
        
        if 'sugar_range' in market_range:
            sugar_range = market_range['sugar_range']
            if not (sugar_range[0] * 0.2 <= sugar_per_100g <= sugar_range[1] * 3):
                concerns.append(f"Sugar content ({sugar_per_100g:.1f}g/100g) outside typical range ({sugar_range})")
        
        if 'fiber_range' in market_range:
            fiber_range = market_range['fiber_range']
            if fiber_per_100g > fiber_range[1] * 3:
                concerns.append(f"Fiber content ({fiber_per_100g:.1f}g/100g) suspiciously high")
        
        if 'sodium_range' in market_range:
            sodium_range = market_range['sodium_range']
            if sodium_per_100g > sodium_range[1] * 2:
                concerns.append(f"Sodium content ({sodium_per_100g:.0f}mg/100g) suspiciously high")
        
        is_realistic = len(concerns) == 0
        return is_realistic, concerns


class ServingSizeValidator:
    """Validate serving size for fraud detection"""
    
    # Typical serving sizes by category (in grams)
    TYPICAL_SERVING_SIZES = {
        'cookies': 30,
        'bread': 50,
        'cereal': 40,
        'juice': 240,
        'yogurt': 200,
        'snack_bar': 35,
        'chips': 28,
        'chocolate': 30,
    }
    
    def validate_serving_size(self, serving_size_g: float, category: str) -> Tuple[bool, str]:
        """
        Validate if serving size is realistic
        
        Args:
            serving_size_g: Declared serving size
            category: Food category
            
        Returns:
            Tuple of (is_valid, reason)
        """
        typical = self.TYPICAL_SERVING_SIZES.get(category.lower())
        
        if not typical:
            return True, "No typical size data"
        
        # Allow 50%-300% of typical
        min_reasonable = typical * 0.5
        max_reasonable = typical * 3
        
        if serving_size_g < min_reasonable:
            return False, f"Serving size ({serving_size_g}g) unusually small compared to typical ({typical}g)"
        elif serving_size_g > max_reasonable:
            return False, f"Serving size ({serving_size_g}g) unusually large compared to typical ({typical}g)"
        
        return True, "Serving size is reasonable"
    
    def calculate_manipulated_servings(self, serving_size_g: float, category: str) -> Dict:
        """
        Calculate how serving size manipulation affects perception
        
        Args:
            serving_size_g: Declared serving size
            category: Food category
            
        Returns:
            Dictionary with manipulation analysis
        """
        typical = self.TYPICAL_SERVING_SIZES.get(category.lower(), serving_size_g)
        
        actual_typical_servings = serving_size_g / typical if typical > 0 else 1
        
        return {
            'declared_serving_g': serving_size_g,
            'typical_serving_g': typical,
            'manipulation_factor': round(actual_typical_servings, 2),
            'perception_impact': f"Declared serving contains ~{actual_typical_servings:.1f}x typical portions",
        }


class IngredientConsistencyValidator:
    """Validate consistency between ingredients and nutrition facts"""
    
    def __init__(self):
        # Ingredient types and their typical caloric contribution
        self.ingredient_calories = {
            'sugar': 387,          # per 100g
            'oil': 884,            # per 100g
            'butter': 717,         # per 100g
            'flour': 364,          # per 100g
            'milk': 61,            # per 100g
            'eggs': 155,           # per 100g
            'nuts': 600,           # average per 100g
            'chocolate': 535,      # per 100g
        }
    
    def validate_ingredient_nutrition_consistency(self, ingredients: IngredientsList,
                                                 nutrition: NutritionFacts,
                                                 serving_size_g: float) -> Tuple[bool, List[str]]:
        """
        Check if declared ingredients are consistent with nutrition facts
        
        Args:
            ingredients: IngredientsList
            nutrition: NutritionFacts
            serving_size_g: Serving size
            
        Returns:
            Tuple of (is_consistent, issues)
        """
        issues = []
        
        # High sugar claim but no sugar ingredients
        if nutrition.sugars_g > 5:
            if not ingredients.sugar_ingredients:
                issues.append("High sugar content declared but no sugar ingredients listed")
        
        # High fat claim but no fat ingredients
        if nutrition.total_fat_g > 10:
            fat_sources = [ing for ing in ingredients.ingredients 
                          if any(x in ing.lower() for x in ['oil', 'butter', 'fat', 'cream'])]
            if not fat_sources:
                issues.append("High fat content declared but no significant fat sources in ingredients")
        
        # Sodium contradiction
        if nutrition.sodium_mg > 200:
            if not ingredients.sodium_ingredients:
                issues.append("High sodium declared but no obvious salt/sodium sources in ingredients")
        
        # Missing allergens
        allergen_keywords = ['milk', 'soy', 'peanut', 'tree nut', 'wheat', 'eggs', 'fish']
        for ing in ingredients.ingredients:
            ing_lower = ing.lower()
            for allergen in allergen_keywords:
                if allergen in ing_lower and allergen not in ingredients.allergens:
                    issues.append(f"Possible allergen '{allergen}' in ingredients but not listed in allergen section")
        
        is_consistent = len(issues) == 0
        return is_consistent, issues


class FraudDetectionEngine:
    """Main fraud detection engine"""
    
    def __init__(self):
        self.market_db = NutritionMarketDatabase()
        self.serving_validator = ServingSizeValidator()
        self.consistency_validator = IngredientConsistencyValidator()
        self.fraud_attempts = 0
        self.fraud_detected = 0
    
    def analyze_for_fraud(self, food_item: FoodItem, category: str) -> FraudDetectionResult:
        """
        Comprehensive fraud detection analysis
        
        Args:
            food_item: FoodItem to analyze
            category: Food category
            
        Returns:
            FraudDetectionResult with findings
        """
        self.fraud_attempts += 1
        
        result = FraudDetectionResult(item_id=food_item.item_id)
        
        # 1. Check nutrition facts realism
        realistic, concerns = self.market_db.is_realistic(food_item.nutrition_facts, category)
        if not realistic:
            result.unrealistic_nutrition_claim = True
            result.fraud_flags.extend(concerns)
        
        # 2. Validate serving size
        valid_serving, serving_reason = self.serving_validator.validate_serving_size(
            food_item.nutrition_facts.serving_size_grams, category
        )
        if not valid_serving:
            result.serving_size_manipulation = True
            result.fraud_flags.append(serving_reason)
        
        # 3. Check ingredient-nutrition consistency
        consistent, consistency_issues = self.consistency_validator.validate_ingredient_nutrition_consistency(
            food_item.ingredients,
            food_item.nutrition_facts,
            food_item.nutrition_facts.serving_size_grams
        )
        if not consistent:
            result.inconsistent_nutrition = True
            result.fraud_flags.extend(consistency_issues)
        
        # 4. Check for missing allergens
        if not food_item.ingredients.allergens and food_item.ingredients.ingredients:
            result.missing_ingredient_allergen = True
            result.fraud_flags.append("No allergen information provided despite having ingredients")
        
        # Calculate fraud confidence
        fraud_indicators = sum([
            result.unrealistic_nutrition_claim,
            result.serving_size_manipulation,
            result.inconsistent_nutrition,
            result.missing_ingredient_allergen,
        ])
        
        result.fraud_confidence = min(0.95, fraud_indicators * 0.25)
        
        # Generate details
        result.details = self._generate_fraud_details(result, food_item, category)
        
        # Get market comparison data
        result.market_range = self.market_db.get_market_range(category)
        
        if result.fraud_confidence > 0.3:
            self.fraud_detected += 1
        
        return result
    
    def _generate_fraud_details(self, result: FraudDetectionResult,
                               food_item: FoodItem, category: str) -> str:
        """Generate detailed fraud analysis report"""
        
        details = f"Fraud Detection Analysis for {food_item.name}\n"
        details += f"Category: {category}\n"
        details += f"Fraud Confidence: {result.fraud_confidence:.1%}\n\n"
        
        if result.fraud_flags:
            details += "🚨 RED FLAGS:\n"
            for flag in result.fraud_flags:
                details += f"  • {flag}\n"
        else:
            details += "✓ No major fraud indicators detected\n"
        
        # Serving size analysis
        serving_analysis = self.serving_validator.calculate_manipulated_servings(
            food_item.nutrition_facts.serving_size_grams, category
        )
        details += f"\nServing Size Analysis:\n"
        details += f"  Declared: {serving_analysis['declared_serving_g']}g\n"
        details += f"  Typical: {serving_analysis['typical_serving_g']}g\n"
        details += f"  {serving_analysis['perception_impact']}\n"
        
        # Market comparison
        market_range = self.market_db.get_market_range(category)
        if market_range:
            details += f"\nMarket Range Comparison (per 100g):\n"
            scale = 100 / (food_item.nutrition_facts.serving_size_grams or 100)
            details += f"  Calories: {food_item.nutrition_facts.calories * scale:.0f} (typical: {market_range['calories_range']})\n"
        
        return details
    
    def get_fraud_metrics(self) -> Dict:
        """Get fraud detection metrics"""
        detection_rate = (self.fraud_detected / self.fraud_attempts * 100) if self.fraud_attempts > 0 else 0
        
        return {
            'total_analyzed': self.fraud_attempts,
            'fraud_detected': self.fraud_detected,
            'detection_rate_percent': round(detection_rate, 1),
        }
