"""
Core Analysis Module for PyActivityParser

Implements core data processing and metric calculations inspired by ActivityParser.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CoreAnalysis:
    """
    Core analysis functionality for accelerometer data processing.
    
    Inspired by ActivityParser Parts 1-2: data processing and basic quality assessment.
    """
    
    def __init__(self, sample_rate_seconds: int = 5):
        self.sample_rate_seconds = sample_rate_seconds
        self.data = None
        self.results = {}
        
    def process_data(self, data: pd.DataFrame, metadata: Dict) -> Dict:
        """
        Process accelerometer data through core analysis pipeline.
        
        Args:
            data (pd.DataFrame): Accelerometer data with columns [timestamp, acceleration, imputed]
            metadata (Dict): Metadata about the data
            
        Returns:
            Dict: Analysis results
        """
        logger.info("Starting core data analysis")
        
        self.data = data.copy()
        self.metadata = metadata
        
        # Step 1: Calculate basic metrics
        basic_metrics = self._calculate_basic_metrics()
        
        # Step 2: Detect wear/non-wear periods
        wear_detection = self._detect_wear_periods()
        
        # Step 3: Calculate daily summaries
        daily_summaries = self._calculate_daily_summaries()
        
        # Step 4: Calculate activity intensity levels
        activity_levels = self._calculate_activity_levels()
        
        # Step 5: Quality assessment
        quality_metrics = self._assess_data_quality()
        
        self.results = {
            'basic_metrics': basic_metrics,
            'wear_detection': wear_detection,
            'daily_summaries': daily_summaries,
            'activity_levels': activity_levels,
            'quality_metrics': quality_metrics,
            'processed_data': self.data
        }
        
        logger.info("Core analysis completed")
        return self.results
    
    def _calculate_basic_metrics(self) -> Dict:
        """Calculate basic acceleration metrics."""
        metrics = {}
        
        # Convert mg to g for calculations
        acc_g = self.data['acceleration'] / 1000.0
        
        # Basic statistics
        metrics['mean_acceleration'] = float(acc_g.mean())
        metrics['std_acceleration'] = float(acc_g.std())
        metrics['min_acceleration'] = float(acc_g.min())
        metrics['max_acceleration'] = float(acc_g.max())
        metrics['median_acceleration'] = float(acc_g.median())
        
        # Calculate additional metrics inspired by ActivityParser
        # Moving averages (5-minute windows)
        window_size = max(1, 300 // self.sample_rate_seconds)  # 5 minutes
        metrics['rolling_mean_5min'] = acc_g.rolling(window=window_size, min_periods=1).mean()
        metrics['rolling_std_5min'] = acc_g.rolling(window=window_size, min_periods=1).std()
        
        # Activity counts (simplified version of ActivityParser's approach)
        # High activity: > 100mg
        # Moderate activity: 40-100mg  
        # Light activity: 5-40mg
        # Sedentary: < 5mg
        acc_mg = self.data['acceleration']
        metrics['high_activity_count'] = (acc_mg > 100).sum()
        metrics['moderate_activity_count'] = ((acc_mg >= 40) & (acc_mg <= 100)).sum()
        metrics['light_activity_count'] = ((acc_mg >= 5) & (acc_mg < 40)).sum()
        metrics['sedentary_count'] = (acc_mg < 5).sum()
        
        return metrics
    
    def _detect_wear_periods(self) -> Dict:
        """
        Detect wear and non-wear periods.
        
        Based on consecutive periods of low/zero acceleration.
        """
        # Simple wear detection: periods with very low variance may indicate non-wear
        window_size = max(1, 1800 // self.sample_rate_seconds)  # 30 minutes
        
        rolling_std = self.data['acceleration'].rolling(
            window=window_size, min_periods=1
        ).std().fillna(0)
        
        # Non-wear threshold: very low standard deviation
        non_wear_threshold = 1.0  # mg
        non_wear_periods = rolling_std < non_wear_threshold
        
        # Mark wear status
        self.data['wear_status'] = ~non_wear_periods
        
        wear_stats = {
            'total_wear_time_hours': float(self.data['wear_status'].sum() * self.sample_rate_seconds / 3600),
            'total_non_wear_time_hours': float((~self.data['wear_status']).sum() * self.sample_rate_seconds / 3600),
            'wear_percentage': float(self.data['wear_status'].mean() * 100),
            'non_wear_periods': self._identify_continuous_periods(~self.data['wear_status'])
        }
        
        return wear_stats
    
    def _identify_continuous_periods(self, mask: pd.Series) -> List[Dict]:
        """Identify continuous periods where mask is True."""
        periods = []
        if mask.sum() == 0:
            return periods
            
        # Find start and end of continuous periods
        mask_diff = mask.astype(int).diff()
        starts = mask_diff[mask_diff == 1].index
        ends = mask_diff[mask_diff == -1].index
        
        # Handle edge cases
        if mask.iloc[0]:
            starts = [mask.index[0]] + list(starts)
        if mask.iloc[-1]:
            ends = list(ends) + [mask.index[-1]]
            
        for start_idx, end_idx in zip(starts, ends):
            start_time = self.data.loc[start_idx, 'timestamp'] if 'timestamp' in self.data.columns else start_idx
            end_time = self.data.loc[end_idx, 'timestamp'] if 'timestamp' in self.data.columns else end_idx
            duration_minutes = (end_idx - start_idx + 1) * self.sample_rate_seconds / 60
            
            periods.append({
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': duration_minutes
            })
            
        return periods
    
    def _calculate_daily_summaries(self) -> List[Dict]:
        """Calculate daily summary statistics."""
        if 'timestamp' not in self.data.columns:
            return []
            
        daily_summaries = []
        
        # Group data by date
        self.data['date'] = pd.to_datetime(self.data['timestamp']).dt.date
        
        for date, day_data in self.data.groupby('date'):
            wear_data = day_data[day_data['wear_status']]
            
            if len(wear_data) == 0:
                continue
                
            summary = {
                'date': date,
                'total_samples': len(day_data),
                'wear_samples': len(wear_data),
                'wear_time_hours': len(wear_data) * self.sample_rate_seconds / 3600,
                'mean_acceleration': float(wear_data['acceleration'].mean()),
                'max_acceleration': float(wear_data['acceleration'].max()),
                'imputed_samples': int(day_data['imputed'].sum()),
                'data_completeness': len(wear_data) / len(day_data) if len(day_data) > 0 else 0
            }
            
            # Activity level breakdown for the day
            acc = wear_data['acceleration']
            summary['high_activity_minutes'] = ((acc > 100).sum() * self.sample_rate_seconds) / 60
            summary['moderate_activity_minutes'] = (((acc >= 40) & (acc <= 100)).sum() * self.sample_rate_seconds) / 60
            summary['light_activity_minutes'] = (((acc >= 5) & (acc < 40)).sum() * self.sample_rate_seconds) / 60
            summary['sedentary_minutes'] = ((acc < 5).sum() * self.sample_rate_seconds) / 60
            
            daily_summaries.append(summary)
            
        return daily_summaries
    
    def _calculate_activity_levels(self) -> Dict:
        """Calculate overall activity level metrics."""
        wear_data = self.data[self.data['wear_status']]
        
        if len(wear_data) == 0:
            return {}
            
        acc = wear_data['acceleration']
        total_wear_time_minutes = len(wear_data) * self.sample_rate_seconds / 60
        
        activity_levels = {
            'total_wear_time_minutes': total_wear_time_minutes,
            'high_activity_percentage': float(((acc > 100).sum() / len(wear_data)) * 100),
            'moderate_activity_percentage': float((((acc >= 40) & (acc <= 100)).sum() / len(wear_data)) * 100),
            'light_activity_percentage': float((((acc >= 5) & (acc < 40)).sum() / len(wear_data)) * 100),
            'sedentary_percentage': float(((acc < 5).sum() / len(wear_data)) * 100),
            'mvpa_minutes': float(((acc >= 40).sum() * self.sample_rate_seconds) / 60),  # Moderate-to-vigorous physical activity
            'average_daily_steps_estimate': self._estimate_daily_steps(wear_data)
        }
        
        return activity_levels
    
    def _estimate_daily_steps(self, wear_data: pd.DataFrame) -> float:
        """
        Rough estimate of daily steps based on acceleration patterns.
        
        This is a simplified approach - in practice, step detection requires
        more sophisticated algorithms.
        """
        # Simple step estimation based on acceleration peaks
        # This is a very rough approximation
        acc = wear_data['acceleration']
        
        # Look for acceleration peaks that might indicate steps
        # Threshold and spacing based on typical walking patterns
        threshold = 50  # mg
        min_step_interval = max(1, int(0.5 / self.sample_rate_seconds))  # 0.5 seconds minimum between steps
        
        peaks = []
        last_peak_idx = -min_step_interval
        
        for i, value in enumerate(acc):
            if value > threshold and (i - last_peak_idx) >= min_step_interval:
                peaks.append(i)
                last_peak_idx = i
        
        # Estimate daily steps (very rough)
        total_wear_time_hours = len(wear_data) * self.sample_rate_seconds / 3600
        if total_wear_time_hours > 0:
            steps_per_hour = len(peaks) / total_wear_time_hours
            estimated_daily_steps = steps_per_hour * 16  # Assume 16 hours of activity per day
        else:
            estimated_daily_steps = 0
            
        return float(estimated_daily_steps)
    
    def _assess_data_quality(self) -> Dict:
        """Assess overall data quality."""
        quality_metrics = {
            'total_recording_hours': len(self.data) * self.sample_rate_seconds / 3600,
            'data_completeness_percentage': float((1 - self.data['acceleration'].isna().sum() / len(self.data)) * 100),
            'imputation_percentage': float((self.data['imputed'].sum() / len(self.data)) * 100),
            'wear_compliance_percentage': float(self.data['wear_status'].mean() * 100),
            'valid_days': len([d for d in self._calculate_daily_summaries() if d['wear_time_hours'] >= 10]),  # Days with ≥10h wear time
            'outlier_count': int((self.data['acceleration'] > 1000).sum()),  # Values > 1g might be outliers
            'zero_values_count': int((self.data['acceleration'] == 0).sum())
        }
        
        # Overall quality score (0-100)
        quality_score = (
            quality_metrics['data_completeness_percentage'] * 0.3 +
            quality_metrics['wear_compliance_percentage'] * 0.4 +
            max(0, 100 - quality_metrics['imputation_percentage']) * 0.2 +
            min(100, quality_metrics['valid_days'] * 20) * 0.1  # Up to 5 valid days
        )
        
        quality_metrics['overall_quality_score'] = round(quality_score, 1)
        
        return quality_metrics