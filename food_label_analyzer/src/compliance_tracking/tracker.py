"""
Compliance Tracking and Caregiver Reporting Module
Tracks user consumption patterns and generates weekly reports for doctors/caregivers
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import field, asdict
from collections import defaultdict
try:
    from food_label_analyzer.src.config import (
        ComplianceReport, FoodItem, UserProfile, MealSimulationResult,
    )
except ImportError:
    from src.config import (
        ComplianceReport, FoodItem, UserProfile, MealSimulationResult,
    )


class DailyConsumptionTracker:
    """Tracks daily food consumption"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.daily_logs: Dict[str, List[FoodItem]] = defaultdict(list)  # Date -> Foods
        self.daily_metrics: Dict[str, Dict] = {}  # Date -> Aggregated metrics
    
    def log_food(self, food_item: FoodItem, date: Optional[datetime] = None):
        """
        Log a food item consumption
        
        Args:
            food_item: Food item consumed
            date: Date of consumption (default: today)
        """
        if date is None:
            date = datetime.now()
        
        date_key = date.strftime("%Y-%m-%d")
        self.daily_logs[date_key].append(food_item)
        
        # Invalidate cached metrics for this date
        if date_key in self.daily_metrics:
            del self.daily_metrics[date_key]
    
    def get_daily_metrics(self, date: datetime, 
                         user_profile: Optional[UserProfile] = None) -> Dict:
        """
        Get aggregated metrics for a day
        
        Args:
            date: Date to get metrics for
            user_profile: Optional user profile for thresholds
            
        Returns:
            Dictionary with daily metrics
        """
        date_key = date.strftime("%Y-%m-%d")
        
        # Return cached if available
        if date_key in self.daily_metrics:
            return self.daily_metrics[date_key]
        
        foods = self.daily_logs.get(date_key, [])
        
        metrics = {
            'date': date_key,
            'food_count': len(foods),
            'total_calories': 0.0,
            'total_carbs_g': 0.0,
            'total_sugars_g': 0.0,
            'total_sodium_mg': 0.0,
            'total_fiber_g': 0.0,
            'total_protein_g': 0.0,
        }
        
        # Aggregate metrics
        for food in foods:
            n = food.nutrition_facts
            metrics['total_calories'] += n.calories
            metrics['total_carbs_g'] += n.total_carbs_g
            metrics['total_sugars_g'] += n.sugars_g
            metrics['total_sodium_mg'] += n.sodium_mg
            metrics['total_fiber_g'] += n.dietary_fiber_g
            metrics['total_protein_g'] += n.protein_g
        
        # Calculate thresholds
        if user_profile:
            metrics['sugar_exceeds'] = metrics['total_sugars_g'] > (user_profile.max_daily_sugar_g or 25)
            metrics['sodium_exceeds'] = metrics['total_sodium_mg'] > (user_profile.max_daily_sodium_mg or 2300)
            metrics['calorie_exceeds'] = metrics['total_calories'] > (user_profile.max_daily_calories or 2000)
        
        self.daily_metrics[date_key] = metrics
        return metrics
    
    def get_date_range_metrics(self, start_date: datetime, end_date: datetime,
                              user_profile: Optional[UserProfile] = None) -> Dict:
        """
        Get aggregated metrics for a date range
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            user_profile: Optional user profile
            
        Returns:
            Dictionary with aggregated metrics
        """
        all_foods = []
        date_range_metrics = {
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
            'total_days': 0,
            'days_with_logs': 0,
            'total_calories': 0.0,
            'total_carbs_g': 0.0,
            'total_sugars_g': 0.0,
            'total_sodium_mg': 0.0,
            'total_fiber_g': 0.0,
            'total_protein_g': 0.0,
            'daily_summaries': {},
        }
        
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            date_range_metrics['total_days'] += 1
            
            daily_metrics = self.get_daily_metrics(current_date, user_profile)
            
            if daily_metrics['food_count'] > 0:
                date_range_metrics['days_with_logs'] += 1
                
                # Accumulate metrics
                date_range_metrics['total_calories'] += daily_metrics['total_calories']
                date_range_metrics['total_carbs_g'] += daily_metrics['total_carbs_g']
                date_range_metrics['total_sugars_g'] += daily_metrics['total_sugars_g']
                date_range_metrics['total_sodium_mg'] += daily_metrics['total_sodium_mg']
                date_range_metrics['total_fiber_g'] += daily_metrics['total_fiber_g']
                date_range_metrics['total_protein_g'] += daily_metrics['total_protein_g']
                
                # Store daily summary
                date_range_metrics['daily_summaries'][date_key] = {
                    'food_count': daily_metrics['food_count'],
                    'calories': round(daily_metrics['total_calories'], 0),
                    'sugars_g': round(daily_metrics['total_sugars_g'], 1),
                    'sodium_mg': round(daily_metrics['total_sodium_mg'], 0),
                }
            
            current_date += timedelta(days=1)
        
        # Calculate averages
        if date_range_metrics['days_with_logs'] > 0:
            div = date_range_metrics['days_with_logs']
            date_range_metrics['avg_daily_calories'] = round(date_range_metrics['total_calories'] / div, 0)
            date_range_metrics['avg_daily_sugars_g'] = round(date_range_metrics['total_sugars_g'] / div, 1)
            date_range_metrics['avg_daily_sodium_mg'] = round(date_range_metrics['total_sodium_mg'] / div, 0)
        
        return date_range_metrics


class ComplianceReportGenerator:
    """Generates compliance reports for caregivers/doctors"""
    
    def __init__(self, tracker: DailyConsumptionTracker):
        self.tracker = tracker
    
    def generate_weekly_report(self, user_profile: UserProfile,
                              report_end_date: Optional[datetime] = None) -> ComplianceReport:
        """
        Generate weekly compliance report
        
        Args:
            user_profile: User profile with medical information
            report_end_date: End date of report (default: today)
            
        Returns:
            ComplianceReport for caregiver/doctor
        """
        if report_end_date is None:
            report_end_date = datetime.now()
        
        report_start_date = report_end_date - timedelta(days=6)  # 7 days total
        
        # Get metrics for the week
        week_metrics = self.tracker.get_date_range_metrics(
            report_start_date, report_end_date, user_profile
        )
        
        report = ComplianceReport(
            user_id=user_profile.user_id,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
        )
        
        # Track compliant meals
        compliant_days = 0
        total_logging_days = week_metrics['days_with_logs']
        
        sugar_threshold_violations = 0
        sodium_threshold_violations = 0
        
        # Check each day for violations
        for date_str, daily_summary in week_metrics['daily_summaries'].items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            daily_metrics = self.tracker.get_daily_metrics(date_obj, user_profile)
            
            # Check thresholds
            sugar_compliant = daily_metrics.get('total_sugars_g', 0) <= (user_profile.max_daily_sugar_g or 25)
            sodium_compliant = daily_metrics.get('total_sodium_mg', 0) <= (user_profile.max_daily_sodium_mg or 2300)
            
            if not sugar_compliant:
                sugar_threshold_violations += 1
            if not sodium_compliant:
                sodium_threshold_violations += 1
            
            if sugar_compliant and sodium_compliant:
                compliant_days += 1
        
        # Populate report
        report.total_meals_logged = sum([daily['food_count'] for daily in week_metrics['daily_summaries'].values()])
        report.compliant_meals_count = compliant_days
        report.compliance_percentage = (compliant_days / total_logging_days * 100) if total_logging_days > 0 else 0
        
        report.average_daily_sugar_g = week_metrics.get('avg_daily_sugars_g', 0)
        report.average_daily_sodium_mg = week_metrics.get('avg_daily_sodium_mg', 0)
        report.average_daily_calories = week_metrics.get('avg_daily_calories', 0)
        
        report.sugar_threshold_violations = sugar_threshold_violations
        report.sodium_threshold_violations = sodium_threshold_violations
        
        # Generate summary text
        report.summary_text = self._generate_summary_text(report, user_profile, week_metrics)
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(report, user_profile)
        
        return report
    
    def _generate_summary_text(self, report: ComplianceReport, 
                              user_profile: UserProfile,
                              week_metrics: Dict) -> str:
        """Generate human-readable summary"""
        
        summary = f"Weekly Compliance Report for {user_profile.user_id}\n"
        summary += f"Period: {report.report_start_date.strftime('%Y-%m-%d')} to {report.report_end_date.strftime('%Y-%m-%d')}\n"
        summary += "=" * 70 + "\n\n"
        
        summary += f"LOGGING COMPLIANCE:\n"
        summary += f"  Days logged: {len(week_metrics['daily_summaries'])} out of 7\n"
        summary += f"  Total meals logged: {report.total_meals_logged}\n"
        summary += f"  Compliant meals: {report.compliant_meals_count}\n"
        summary += f"  Overall compliance: {report.compliance_percentage:.0f}%\n\n"
        
        summary += f"WEEKLY TOTALS:\n"
        summary += f"  Calories: {week_metrics['total_calories']:.0f}\n"
        summary += f"  Carbohydrates: {week_metrics['total_carbs_g']:.0f}g\n"
        summary += f"  Sugars: {week_metrics['total_sugars_g']:.0f}g\n"
        summary += f"  Sodium: {week_metrics['total_sodium_mg']:.0f}mg\n"
        summary += f"  Fiber: {week_metrics['total_fiber_g']:.0f}g\n"
        summary += f"  Protein: {week_metrics['total_protein_g']:.0f}g\n\n"
        
        summary += f"DAILY AVERAGES:\n"
        summary += f"  Calories: {week_metrics.get('avg_daily_calories', 0):.0f}/day"
        daily_sugar_allowance = user_profile.max_daily_sugar_g or 25
        summary += f" (target: {user_profile.max_daily_calories or 2000})\n"
        summary += f"  Sugars: {report.average_daily_sugar_g:.1f}g/day (target: {daily_sugar_allowance}g, violations: {report.sugar_threshold_violations})\n"
        
        daily_sodium_allowance = user_profile.max_daily_sodium_mg or 2300
        summary += f"  Sodium: {report.average_daily_sodium_mg:.0f}mg/day (target: {daily_sodium_allowance}mg, violations: {report.sodium_threshold_violations})\n\n"
        
        # Medical assessment
        if user_profile.has_diabetes:
            summary += f"DIABETES MANAGEMENT:\n"
            summary += f"  Average daily sugars: {report.average_daily_sugar_g:.1f}g\n"
            if report.sugar_threshold_violations == 0:
                summary += "  ✓ Sugar intake within recommended range for the week\n"
            else:
                summary += f"  ⚠️  {report.sugar_threshold_violations} days exceeded sugar target\n"
        
        if user_profile.hypertension_severity.value != 'normal':
            summary += f"HYPERTENSION MANAGEMENT:\n"
            summary += f"  Average daily sodium: {report.average_daily_sodium_mg:.0f}mg\n"
            if report.sodium_threshold_violations == 0:
                summary += "  ✓ Sodium intake within recommended range for the week\n"
            else:
                summary += f"  ⚠️  {report.sodium_threshold_violations} days exceeded sodium target\n"
        
        summary += "\n" + "=" * 70 + "\n"
        
        return summary
    
    def _generate_recommendations(self, report: ComplianceReport,
                                 user_profile: UserProfile) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Logging compliance
        if report.compliance_percentage < 50:
            recommendations.append("⚠️  Increase dietary logging consistency - aim for daily tracking")
        
        # Sugar recommendations
        if user_profile.has_diabetes:
            if report.average_daily_sugar_g > (user_profile.max_daily_sugar_g or 25):
                recommendations.append(f"Reduce average daily sugar intake to below {user_profile.max_daily_sugar_g or 25}g")
            if report.sugar_threshold_violations > 3:
                recommendations.append("Focus on foods with <5g sugar per serving; consult nutritionist for meal planning")
        
        # Sodium recommendations
        if user_profile.hypertension_severity.value != 'normal':
            if report.average_daily_sodium_mg > (user_profile.max_daily_sodium_mg or 2300):
                recommendations.append(f"Reduce average daily sodium to below {user_profile.max_daily_sodium_mg or 2300}mg")
            if report.sodium_threshold_violations > 3:
                recommendations.append("Limit processed foods; choose fresh foods and low-sodium alternatives")
        
        # General recommendations
        if report.compliance_percentage >= 75:
            recommendations.append("✓ Good compliance this week - maintain current dietary habits")
        
        return recommendations[:5]  # Top 5 recommendations
