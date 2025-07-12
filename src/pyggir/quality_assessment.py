"""
Quality Assessment Module for PyGGIR

Provides data quality evaluation and validation metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class QualityAssessment:
    """
    Data quality assessment and validation.
    
    Inspired by GGIR's quality check procedures.
    """
    
    def __init__(self):
        self.quality_thresholds = {
            'min_wear_hours_per_day': 10,
            'min_valid_days': 4,
            'max_imputation_percentage': 20,
            'max_outlier_percentage': 1
        }
    
    def assess_quality(self, data: pd.DataFrame, metadata: Dict, analysis_results: Dict) -> Dict:
        """
        Comprehensive quality assessment of accelerometer data.
        
        Args:
            data (pd.DataFrame): Processed accelerometer data
            metadata (Dict): Data metadata
            analysis_results (Dict): Results from core analysis
            
        Returns:
            Dict: Quality assessment results
        """
        logger.info("Performing quality assessment")
        
        quality_report = {
            'participant_id': metadata.get('participant_id', 'unknown'),
            'assessment_timestamp': pd.Timestamp.now(),
            'data_overview': self._assess_data_overview(data, metadata),
            'wear_compliance': self._assess_wear_compliance(analysis_results),
            'data_integrity': self._assess_data_integrity(data),
            'activity_patterns': self._assess_activity_patterns(analysis_results),
            'recommendations': []
        }
        
        # Generate overall quality score and recommendations
        quality_report['overall_assessment'] = self._generate_overall_assessment(quality_report)
        quality_report['recommendations'] = self._generate_recommendations(quality_report)
        
        return quality_report
    
    def _assess_data_overview(self, data: pd.DataFrame, metadata: Dict) -> Dict:
        """Assess basic data characteristics."""
        return {
            'recording_duration_days': (metadata.get('end_time', metadata.get('start_time')) - 
                                      metadata.get('start_time')).days if metadata.get('start_time') else 0,
            'total_samples': len(data),
            'expected_samples': metadata.get('expected_samples', 0),
            'sample_rate_seconds': metadata.get('sample_rate_seconds', 5),
            'data_completeness': 1 - (data['acceleration'].isna().sum() / len(data)),
            'file_size_mb': len(data) * 8 / (1024 * 1024)  # Rough estimate
        }
    
    def _assess_wear_compliance(self, analysis_results: Dict) -> Dict:
        """Assess device wear compliance."""
        wear_detection = analysis_results.get('wear_detection', {})
        daily_summaries = analysis_results.get('daily_summaries', [])
        
        valid_days = [day for day in daily_summaries 
                     if day.get('wear_time_hours', 0) >= self.quality_thresholds['min_wear_hours_per_day']]
        
        compliance = {
            'total_wear_time_hours': wear_detection.get('total_wear_time_hours', 0),
            'wear_percentage': wear_detection.get('wear_percentage', 0),
            'valid_days_count': len(valid_days),
            'total_days': len(daily_summaries),
            'meets_minimum_wear': len(valid_days) >= self.quality_thresholds['min_valid_days'],
            'average_daily_wear_hours': np.mean([day.get('wear_time_hours', 0) for day in daily_summaries]) if daily_summaries else 0,
            'non_wear_periods': wear_detection.get('non_wear_periods', [])
        }
        
        # Flag long non-wear periods (>2 hours)
        long_non_wear_periods = [period for period in compliance['non_wear_periods'] 
                                if period.get('duration_minutes', 0) > 120]
        compliance['long_non_wear_periods_count'] = len(long_non_wear_periods)
        
        return compliance
    
    def _assess_data_integrity(self, data: pd.DataFrame) -> Dict:
        """Assess data integrity and detect anomalies."""
        acc = data['acceleration']
        
        integrity = {
            'missing_values_count': acc.isna().sum(),
            'missing_values_percentage': (acc.isna().sum() / len(acc)) * 100,
            'imputed_values_count': data['imputed'].sum(),
            'imputed_values_percentage': (data['imputed'].sum() / len(data)) * 100,
            'zero_values_count': (acc == 0).sum(),
            'zero_values_percentage': ((acc == 0).sum() / len(acc)) * 100,
            'negative_values_count': (acc < 0).sum(),
            'outliers': self._detect_outliers(acc),
            'data_range': {
                'min': float(acc.min()),
                'max': float(acc.max()),
                'mean': float(acc.mean()),
                'std': float(acc.std())
            }
        }
        
        # Check for unrealistic values
        integrity['unrealistic_values'] = {
            'extremely_high': (acc > 2000).sum(),  # > 2g
            'extremely_low': (acc < -100).sum()    # Negative acceleration
        }
        
        return integrity
    
    def _detect_outliers(self, acceleration: pd.Series) -> Dict:
        """Detect statistical outliers in acceleration data."""
        Q1 = acceleration.quantile(0.25)
        Q3 = acceleration.quantile(0.75)
        IQR = Q3 - Q1
        
        # IQR method
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers_iqr = ((acceleration < lower_bound) | (acceleration > upper_bound)).sum()
        
        # Z-score method
        z_scores = np.abs((acceleration - acceleration.mean()) / acceleration.std())
        outliers_zscore = (z_scores > 3).sum()
        
        return {
            'iqr_method': {
                'count': int(outliers_iqr),
                'percentage': float((outliers_iqr / len(acceleration)) * 100),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound)
            },
            'zscore_method': {
                'count': int(outliers_zscore),
                'percentage': float((outliers_zscore / len(acceleration)) * 100)
            }
        }
    
    def _assess_activity_patterns(self, analysis_results: Dict) -> Dict:
        """Assess activity pattern characteristics."""
        activity_levels = analysis_results.get('activity_levels', {})
        daily_summaries = analysis_results.get('daily_summaries', [])
        
        patterns = {
            'sedentary_percentage': activity_levels.get('sedentary_percentage', 0),
            'light_activity_percentage': activity_levels.get('light_activity_percentage', 0),
            'moderate_activity_percentage': activity_levels.get('moderate_activity_percentage', 0),
            'high_activity_percentage': activity_levels.get('high_activity_percentage', 0),
            'mvpa_minutes_total': activity_levels.get('mvpa_minutes', 0),
            'estimated_daily_steps': activity_levels.get('average_daily_steps_estimate', 0)
        }
        
        # Calculate daily variability
        if daily_summaries:
            daily_means = [day.get('mean_acceleration', 0) for day in daily_summaries]
            patterns['daily_variability'] = {
                'mean_acceleration_std': float(np.std(daily_means)),
                'mean_acceleration_cv': float(np.std(daily_means) / np.mean(daily_means)) if np.mean(daily_means) > 0 else 0
            }
        
        # Activity pattern flags
        patterns['flags'] = {
            'extremely_sedentary': patterns['sedentary_percentage'] > 95,
            'very_low_activity': patterns['light_activity_percentage'] + patterns['moderate_activity_percentage'] + patterns['high_activity_percentage'] < 5,
            'unrealistic_high_activity': patterns['high_activity_percentage'] > 50
        }
        
        return patterns
    
    def _generate_overall_assessment(self, quality_report: Dict) -> Dict:
        """Generate overall quality assessment and score."""
        scores = {}
        
        # Data completeness score (0-100)
        data_completeness = quality_report['data_overview']['data_completeness']
        scores['data_completeness'] = min(100, data_completeness * 100)
        
        # Wear compliance score (0-100)
        wear_compliance = quality_report['wear_compliance']
        compliance_score = 0
        if wear_compliance['meets_minimum_wear']:
            compliance_score += 50
        compliance_score += min(50, wear_compliance['wear_percentage'] / 2)
        scores['wear_compliance'] = compliance_score
        
        # Data integrity score (0-100)
        integrity = quality_report['data_integrity']
        integrity_score = 100
        integrity_score -= min(30, integrity['imputed_values_percentage'])
        integrity_score -= min(20, integrity['outliers']['iqr_method']['percentage'] * 10)
        integrity_score -= min(20, integrity['missing_values_percentage'] * 2)
        scores['data_integrity'] = max(0, integrity_score)
        
        # Activity pattern score (0-100)
        patterns = quality_report['activity_patterns']
        pattern_score = 100
        if patterns['flags']['extremely_sedentary']:
            pattern_score -= 30
        if patterns['flags']['very_low_activity']:
            pattern_score -= 40
        if patterns['flags']['unrealistic_high_activity']:
            pattern_score -= 50
        scores['activity_patterns'] = max(0, pattern_score)
        
        # Overall score (weighted average)
        overall_score = (
            scores['data_completeness'] * 0.25 +
            scores['wear_compliance'] * 0.35 +
            scores['data_integrity'] * 0.25 +
            scores['activity_patterns'] * 0.15
        )
        
        assessment = {
            'individual_scores': scores,
            'overall_score': round(overall_score, 1),
            'quality_grade': self._get_quality_grade(overall_score),
            'data_usable': overall_score >= 60  # Minimum threshold for usable data
        }
        
        return assessment
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(self, quality_report: Dict) -> List[str]:
        """Generate recommendations based on quality assessment."""
        recommendations = []
        
        wear_compliance = quality_report['wear_compliance']
        integrity = quality_report['data_integrity']
        patterns = quality_report['activity_patterns']
        overall = quality_report['overall_assessment']
        
        # Wear compliance recommendations
        if not wear_compliance['meets_minimum_wear']:
            recommendations.append(
                f"Insufficient wear time: Only {wear_compliance['valid_days_count']} valid days. "
                f"Recommend minimum {self.quality_thresholds['min_valid_days']} days with "
                f"≥{self.quality_thresholds['min_wear_hours_per_day']} hours wear time."
            )
        
        if wear_compliance['long_non_wear_periods_count'] > 0:
            recommendations.append(
                f"Found {wear_compliance['long_non_wear_periods_count']} extended non-wear periods (>2h). "
                "Consider participant compliance coaching."
            )
        
        # Data integrity recommendations
        if integrity['imputed_values_percentage'] > self.quality_thresholds['max_imputation_percentage']:
            recommendations.append(
                f"High imputation rate ({integrity['imputed_values_percentage']:.1f}%). "
                "Check data collection procedures and device functionality."
            )
        
        if integrity['outliers']['iqr_method']['percentage'] > self.quality_thresholds['max_outlier_percentage']:
            recommendations.append(
                f"High outlier rate ({integrity['outliers']['iqr_method']['percentage']:.1f}%). "
                "Consider data cleaning or investigate device issues."
            )
        
        # Activity pattern recommendations
        if patterns['flags']['extremely_sedentary']:
            recommendations.append(
                "Extremely high sedentary time (>95%). Verify device placement and participant instructions."
            )
        
        if patterns['flags']['unrealistic_high_activity']:
            recommendations.append(
                "Unrealistically high activity levels detected. Check for device malfunction or inappropriate wear."
            )
        
        # Overall recommendations
        if overall['overall_score'] < 60:
            recommendations.append(
                "Overall data quality is poor. Consider excluding from analysis or collecting additional data."
            )
        elif overall['overall_score'] < 80:
            recommendations.append(
                "Data quality is acceptable but could be improved. Consider targeted quality improvement measures."
            )
        
        if not recommendations:
            recommendations.append("Data quality is good. No major issues detected.")
        
        return recommendations