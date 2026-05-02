"""
Food Classification Engine
Classifies foods as Suitable, Moderate, or Avoid based on medical thresholds and user profiles
"""
from typing import Tuple, List, Dict, Optional
try:
    from food_label_analyzer.src.config import (
        FoodClassification, DiabetesType, HypertensionSeverity,
        NutritionFacts, ClinicalMetrics, UserProfile, FoodItem,
        SODIUM_ALERTS, SUGAR_ALERTS, GI_RANGES,
    )
except ImportError:
    from src.config import (
        FoodClassification, DiabetesType, HypertensionSeverity,
        NutritionFacts, ClinicalMetrics, UserProfile, FoodItem,
        SODIUM_ALERTS, SUGAR_ALERTS, GI_RANGES,
    )


class FoodClassifier:
    """Classifies foods based on medical thresholds and user profiles"""
    
    def __init__(self):
        self.classification_thresholds = self._initialize_thresholds()
    
    def _initialize_thresholds(self) -> Dict:
        """Initialize medical classification thresholds"""
        return {
            'diabetes': {
                'type_1': {
                    'max_sugar_per_serving_g': 8,
                    'max_gi': 70,
                    'max_gl_per_serving': 15,
                    'preferred_fiber_g': 3,
                },
                'type_2': {
                    'max_sugar_per_serving_g': 8,
                    'max_gi': 70,
                    'max_gl_per_serving': 20,
                    'preferred_fiber_g': 3,
                },
                'gestational': {
                    'max_sugar_per_serving_g': 5,
                    'max_gi': 55,
                    'max_gl_per_serving': 10,
                    'preferred_fiber_g': 3,
                },
            },
            'hypertension': {
                'normal': {
                    'max_sodium_mg': 400,
                },
                'elevated': {
                    'max_sodium_mg': 300,
                },
                'stage_1': {
                    'max_sodium_mg': 200,
                },
                'stage_2': {
                    'max_sodium_mg': 100,
                },
                'crisis': {
                    'max_sodium_mg': 50,
                },
            },
            'general': {
                'max_saturated_fat_percent': 10,  # % of daily calories
                'max_trans_fat_percent': 1,
                'min_fiber_g': 2,
            }
        }
    
    def classify_food(self, food_item: FoodItem, 
                     user_profile: Optional[UserProfile] = None) -> Tuple[FoodClassification, float, str]:
        """
        Classify a food item for a user
        
        Args:
            food_item: FoodItem with nutrition facts and metrics
            user_profile: Optional user medical profile
            
        Returns:
            Tuple of (classification, confidence_score_0_1, explanation)
        """
        if user_profile:
            return self._classify_with_profile(food_item, user_profile)
        else:
            return self._classify_general(food_item)
    
    def _classify_with_profile(self, food_item: FoodItem, 
                              user_profile: UserProfile) -> Tuple[FoodClassification, float, str]:
        """Classify based on specific user profile"""
        
        warnings = []
        scores = {}
        
        nutrition = food_item.nutrition_facts
        metrics = food_item.clinical_metrics
        
        # DIABETES SCREENING
        if user_profile.has_diabetes:
            diabetes_class, diabetes_score, diabetes_warnings = self._evaluate_diabetes_safety(
                nutrition, metrics, user_profile
            )
            scores['diabetes'] = diabetes_score
            warnings.extend(diabetes_warnings)
        
        # HYPERTENSION SCREENING
        if user_profile.hypertension_severity != HypertensionSeverity.NORMAL:
            hypertension_class, htn_score, htn_warnings = self._evaluate_hypertension_safety(
                nutrition, user_profile
            )
            scores['hypertension'] = htn_score
            warnings.extend(htn_warnings)
        
        # GENERAL NUTRITION SCREENING
        general_class, general_score, general_warnings = self._evaluate_general_nutrition(nutrition)
        scores['general'] = general_score
        warnings.extend(general_warnings)
        
        # Determine overall classification
        min_score = min(scores.values()) if scores else 0.0
        avg_score = sum(scores.values()) / len(scores) if scores else 0.5
        
        # Classification logic
        if min_score >= 0.7:
            classification = FoodClassification.SUITABLE
        elif min_score >= 0.4:
            classification = FoodClassification.MODERATE
        else:
            classification = FoodClassification.AVOID
        
        confidence = min(0.95, avg_score)
        explanation = self._generate_explanation(food_item, user_profile, warnings, classification)
        
        return classification, confidence, explanation
    
    def _classify_general(self, food_item: FoodItem) -> Tuple[FoodClassification, float, str]:
        """General classification without user profile"""
        
        nutrition = food_item.nutrition_facts
        metrics = food_item.clinical_metrics
        
        warnings = []
        score = 0.5
        
        # Sugar check (only if available)
        if nutrition.sugars_g and nutrition.sugars_g > 0:
            if nutrition.sugars_g > SUGAR_ALERTS['high']:
                warnings.append(f"High sugar: {nutrition.sugars_g:.1f}g per serving")
                score -= 0.2
            elif nutrition.sugars_g > SUGAR_ALERTS['medium']:
                warnings.append(f"Moderate sugar: {nutrition.sugars_g:.1f}g per serving")
                score -= 0.1
        
        # Sodium check (only if available)
        if nutrition.sodium_mg and nutrition.sodium_mg > 0:
            if nutrition.sodium_mg > SODIUM_ALERTS['high']:
                warnings.append(f"High sodium: {nutrition.sodium_mg:.0f}mg per serving")
                score -= 0.2
        
        # GI check (only if available)
        if metrics.glycemic_index and metrics.glycemic_index > 0:
            if metrics.glycemic_index > GI_RANGES['high'][0]:
                warnings.append(f"High glycemic index: {metrics.glycemic_index:.0f}")
                score -= 0.15
        
        # Fiber check (only if available)
        if nutrition.dietary_fiber_g and nutrition.dietary_fiber_g > 0:
            if nutrition.dietary_fiber_g >= 2:
                score += 0.1
        
        # Trans fat check (only if available)
        if nutrition.trans_fat_g and nutrition.trans_fat_g > 0:
            warnings.append("Contains trans fats")
            score -= 0.15
        
        score = max(0.0, min(1.0, score))
        
        if score >= 0.7:
            classification = FoodClassification.SUITABLE
        elif score >= 0.4:
            classification = FoodClassification.MODERATE
        else:
            classification = FoodClassification.AVOID
        
        explanation = f"General classification based on available nutrients: {len(warnings)} concerns identified"
        
        return classification, score, explanation
    
    def _evaluate_diabetes_safety(self, nutrition: NutritionFacts, 
                                 metrics: ClinicalMetrics,
                                 user_profile: UserProfile) -> Tuple[float, float, List[str]]:
        """Evaluate safety for diabetic patients"""
        
        warnings = []
        score = 1.0
        
        diabetes_type = user_profile.diabetes_type or DiabetesType.TYPE_2
        thresholds = self.classification_thresholds['diabetes'][diabetes_type.value]
        
        # Sugar evaluation (only if available)
        if nutrition.sugars_g and nutrition.sugars_g > 0:
            if nutrition.sugars_g > thresholds['max_sugar_per_serving_g']:
                warnings.append(f"Exceeds sugar threshold: {nutrition.sugars_g:.1f}g vs {thresholds['max_sugar_per_serving_g']}g max")
                score *= 0.5
        
        # GI evaluation (only if available)
        if metrics.glycemic_index and metrics.glycemic_index > 0:
            if metrics.glycemic_index > thresholds['max_gi']:
                warnings.append(f"High glycemic index: {metrics.glycemic_index:.0f} (>70)")
                score *= 0.6
        
        # GL evaluation (only if available)
        if metrics.glycemic_load and metrics.glycemic_load > 0:
            if metrics.glycemic_load > thresholds['max_gl_per_serving']:
                warnings.append(f"High glycemic load: {metrics.glycemic_load:.1f}")
                score *= 0.7
        
        # Fiber evaluation (only if available)
        if nutrition.dietary_fiber_g and nutrition.dietary_fiber_g > 0:
            if nutrition.dietary_fiber_g >= thresholds['preferred_fiber_g']:
                score *= 1.1  # Bonus for good fiber
        
        # Hidden sugars check (only if available)
        if metrics.risk_factors and any('hidden' in rf.lower() for rf in metrics.risk_factors):
            warnings.append("Contains hidden sugars")
            score *= 0.7
        
        score = max(0.0, min(1.0, score))
        
        return score, warnings
    
    def _evaluate_hypertension_safety(self, nutrition: NutritionFacts,
                                     user_profile: UserProfile) -> Tuple[float, float, List[str]]:
        """Evaluate safety for hypertension patients"""
        
        warnings = []
        score = 1.0
        
        severity = user_profile.hypertension_severity
        thresholds = self.classification_thresholds['hypertension'][severity.value]
        
        # Sodium evaluation (most critical) - only if available
        if nutrition.sodium_mg and nutrition.sodium_mg > 0:
            max_sodium = thresholds['max_sodium_mg']
            if nutrition.sodium_mg > max_sodium:
                warnings.append(f"Exceeds sodium threshold: {nutrition.sodium_mg:.0f}mg vs {max_sodium}mg max")
                excess_percent = ((nutrition.sodium_mg - max_sodium) / max_sodium) * 100
                score *= (1.0 - min(0.8, excess_percent / 100))  # Proportional penalty
        
        # Saturated fat check (cardiovascular risk) - only if available
        if nutrition.saturated_fat_g and nutrition.saturated_fat_g > 2:
            warnings.append(f"High saturated fat: {nutrition.saturated_fat_g:.1f}g")
            score *= 0.85
        
        # Potassium bonus (helps manage BP) - only if available
        if nutrition.potassium_mg and nutrition.potassium_mg > 300:
            warnings.append(f"Good potassium content: {nutrition.potassium_mg:.0f}mg")
            score *= 1.1
        
        score = max(0.0, min(1.0, score))
        
        return score, warnings
    
    def _evaluate_general_nutrition(self, nutrition: NutritionFacts) -> Tuple[float, float, List[str]]:
        """General nutrition evaluation"""
        
        warnings = []
        score = 1.0
        
        # Trans fat check - only if available
        if nutrition.trans_fat_g and nutrition.trans_fat_g > 0:
            warnings.append(f"Contains trans fats: {nutrition.trans_fat_g:.2f}g")
            score *= 0.7
        
        # Saturated fat check - only if available and total fat available
        if nutrition.total_fat_g and nutrition.total_fat_g > 0 and nutrition.saturated_fat_g and nutrition.saturated_fat_g > 0:
            sat_fat_ratio = nutrition.saturated_fat_g / nutrition.total_fat_g
            if sat_fat_ratio > 0.3:
                warnings.append(f"High saturated fat ratio: {sat_fat_ratio:.1%}")
                score *= 0.85
        
        # Fiber check - only if available
        if nutrition.dietary_fiber_g and nutrition.dietary_fiber_g > 0:
            if nutrition.dietary_fiber_g >= 3:
                score *= 1.1
        
        score = max(0.0, min(1.0, score))
        
        return score, warnings
    
    def _generate_explanation(self, food_item: FoodItem, user_profile: UserProfile,
                             warnings: List[str], classification: FoodClassification) -> str:
        """Generate detailed explanation for classification"""
        
        explanation = f"Classification: {classification.value.upper()}\n\n"
        
        # User-specific context
        if user_profile.has_diabetes:
            explanation += f"Diabetes Type: {user_profile.diabetes_type.value.replace('_', ' ')}\n"
        
        if user_profile.hypertension_severity != HypertensionSeverity.NORMAL:
            explanation += f"Hypertension Severity: {user_profile.hypertension_severity.value.replace('_', ' ')}\n"
        
        explanation += f"\nServing Size: {food_item.nutrition_facts.serving_size_grams}g\n"
        explanation += f"Per Serving:\n"
        explanation += f"  • Calories: {food_item.nutrition_facts.calories:.0f}\n"
        explanation += f"  • Carbs: {food_item.nutrition_facts.total_carbs_g:.1f}g\n"
        explanation += f"  • Sugar: {food_item.nutrition_facts.sugars_g:.1f}g\n"
        explanation += f"  • Sodium: {food_item.nutrition_facts.sodium_mg:.0f}mg\n"
        explanation += f"  • Fiber: {food_item.nutrition_facts.dietary_fiber_g:.1f}g\n"
        
        if food_item.clinical_metrics.glycemic_index:
            explanation += f"\nGlycemic Index: {food_item.clinical_metrics.glycemic_index:.0f}\n"
        
        if warnings:
            explanation += f"\n⚠️  CONCERNS:\n"
            for warning in warnings[:3]:  # Top 3 concerns
                explanation += f"  • {warning}\n"
        
        if food_item.clinical_metrics.reasoning_text:
            explanation += f"\nMedical Reasoning:\n{food_item.clinical_metrics.reasoning_text}\n"
        
        return explanation


class ClassificationF1Scorer:
    """Compute F1 scores for classification accuracy"""
    
    def __init__(self):
        self.predictions = []
        self.ground_truth = []
    
    def add_prediction(self, predicted_class: FoodClassification, 
                      true_class: FoodClassification):
        """Add a prediction for evaluation"""
        self.predictions.append(predicted_class)
        self.ground_truth.append(true_class)
    
    def compute_f1(self, target_class: FoodClassification = FoodClassification.AVOID) -> Dict:
        """
        Compute F1 score for target classification
        
        Args:
            target_class: The class to compute F1 for (default: AVOID for high-risk foods)
            
        Returns:
            Dictionary with precision, recall, F1, and support
        """
        if not self.predictions:
            return {}
        
        # Binary classification: target class vs others
        pred_binary = [1 if p == target_class else 0 for p in self.predictions]
        true_binary = [1 if t == target_class else 0 for t in self.ground_truth]
        
        # Calculate TP, FP, FN
        tp = sum([1 for p, t in zip(pred_binary, true_binary) if p == 1 and t == 1])
        fp = sum([1 for p, t in zip(pred_binary, true_binary) if p == 1 and t == 0])
        fn = sum([1 for p, t in zip(pred_binary, true_binary) if p == 0 and t == 1])
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        support = tp + fn
        
        return {
            'target_class': target_class.value,
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1': round(f1, 3),
            'support': support,
            'tp': tp,
            'fp': fp,
            'fn': fn,
        }
    
    def compute_all_metrics(self) -> Dict:
        """Compute F1 scores for all classes"""
        metrics = {
            'avoid': self.compute_f1(FoodClassification.AVOID),
            'moderate': self.compute_f1(FoodClassification.MODERATE),
            'suitable': self.compute_f1(FoodClassification.SUITABLE),
        }
        
        # Macro average F1
        f1_scores = [m['f1'] for m in metrics.values() if 'f1' in m]
        metrics['macro_f1'] = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
        
        return metrics
    
    def reset(self):
        """Reset scorer for new evaluation"""
        self.predictions = []
        self.ground_truth = []
