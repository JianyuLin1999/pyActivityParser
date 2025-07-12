"""
Activity Analysis Module for PyActivityParser

Provides detailed physical activity pattern analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ActivityAnalysis:
    """
    Physical activity pattern analysis.
    
    Inspired by ActivityParser Part 5: activity bout detection and analysis.
    """
    
    def __init__(self, sample_rate_seconds: int = 5):
        self.sample_rate_seconds = sample_rate_seconds
        
        # Activity intensity thresholds (mg)
        self.thresholds = {
            'sedentary': 0,
            'light': 5,
            'moderate': 40,
            'vigorous': 100
        }
        
        # Bout detection parameters
        self.bout_criteria = {
            'min_bout_duration_minutes': 10,
            'interruption_tolerance': 0.2  # Allow 20% interruptions
        }
    
    def analyze_activity_patterns(self, data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """
        Perform comprehensive activity pattern analysis.
        
        Args:
            data (pd.DataFrame): Processed accelerometer data
            analysis_results (Dict): Results from core analysis
            
        Returns:
            Dict: Activity analysis results
        """
        logger.info("Starting activity pattern analysis")
        
        # Filter to wear time only
        wear_data = data[data['wear_status']].copy()
        
        if len(wear_data) == 0:
            logger.warning("No wear time data available for activity analysis")
            return {}
        
        # Activity classification
        activity_classification = self._classify_activity_intensity(wear_data)
        
        # Bout detection
        activity_bouts = self._detect_activity_bouts(wear_data, activity_classification)
        
        # Hourly patterns
        hourly_patterns = self._analyze_hourly_patterns(wear_data)
        
        # Weekly patterns (if data spans multiple days)
        weekly_patterns = self._analyze_weekly_patterns(wear_data)
        
        # Activity transitions
        transitions = self._analyze_activity_transitions(activity_classification)
        
        results = {
            'activity_classification': activity_classification,
            'activity_bouts': activity_bouts,
            'hourly_patterns': hourly_patterns,
            'weekly_patterns': weekly_patterns,
            'activity_transitions': transitions,
            'summary_metrics': self._calculate_summary_metrics(activity_classification, activity_bouts)
        }
        
        logger.info("Activity pattern analysis completed")
        return results
    
    def _classify_activity_intensity(self, data: pd.DataFrame) -> pd.DataFrame:
        """Classify each data point by activity intensity."""
        data = data.copy()
        acc = data['acceleration']
        
        # Classify activity intensity
        conditions = [
            acc < self.thresholds['light'],
            (acc >= self.thresholds['light']) & (acc < self.thresholds['moderate']),
            (acc >= self.thresholds['moderate']) & (acc < self.thresholds['vigorous']),
            acc >= self.thresholds['vigorous']
        ]
        
        choices = ['sedentary', 'light', 'moderate', 'vigorous']
        data['activity_intensity'] = np.select(conditions, choices, default='unknown')
        
        # Calculate intensity code for numerical analysis
        intensity_codes = {'sedentary': 0, 'light': 1, 'moderate': 2, 'vigorous': 3}
        data['intensity_code'] = data['activity_intensity'].map(intensity_codes)
        
        return data
    
    def _detect_activity_bouts(self, data: pd.DataFrame, classified_data: pd.DataFrame) -> Dict:
        """
        Detect sustained activity bouts.
        
        A bout is a period of sustained activity at a given intensity level.
        """
        min_bout_samples = int(self.bout_criteria['min_bout_duration_minutes'] * 60 / self.sample_rate_seconds)
        
        bouts = {
            'moderate_bouts': [],
            'vigorous_bouts': [],
            'mvpa_bouts': [],  # Moderate to vigorous physical activity
            'sedentary_bouts': []
        }
        
        # Detect MVPA bouts (moderate + vigorous)
        mvpa_mask = classified_data['intensity_code'] >= 2
        bouts['mvpa_bouts'] = self._find_bouts(mvpa_mask, min_bout_samples, classified_data)
        
        # Detect moderate intensity bouts
        moderate_mask = classified_data['intensity_code'] == 2
        bouts['moderate_bouts'] = self._find_bouts(moderate_mask, min_bout_samples, classified_data)
        
        # Detect vigorous intensity bouts
        vigorous_mask = classified_data['intensity_code'] == 3
        bouts['vigorous_bouts'] = self._find_bouts(vigorous_mask, min_bout_samples, classified_data)
        
        # Detect sedentary bouts (longer threshold - 30 minutes)
        sedentary_min_samples = int(30 * 60 / self.sample_rate_seconds)
        sedentary_mask = classified_data['intensity_code'] == 0
        bouts['sedentary_bouts'] = self._find_bouts(sedentary_mask, sedentary_min_samples, classified_data)
        
        return bouts
    
    def _find_bouts(self, activity_mask: pd.Series, min_samples: int, data: pd.DataFrame) -> List[Dict]:
        """Find continuous bouts of activity meeting minimum duration."""
        bouts = []
        
        # Find continuous periods
        mask_diff = activity_mask.astype(int).diff()
        starts = mask_diff[mask_diff == 1].index
        ends = mask_diff[mask_diff == -1].index
        
        # Handle edge cases
        if activity_mask.iloc[0]:
            starts = [activity_mask.index[0]] + list(starts)
        if activity_mask.iloc[-1]:
            ends = list(ends) + [activity_mask.index[-1]]
            
        for start_idx, end_idx in zip(starts, ends):
            bout_length = end_idx - start_idx + 1
            
            if bout_length >= min_samples:
                bout_data = data.loc[start_idx:end_idx]
                
                bout = {
                    'start_time': bout_data['timestamp'].iloc[0] if 'timestamp' in bout_data.columns else start_idx,
                    'end_time': bout_data['timestamp'].iloc[-1] if 'timestamp' in bout_data.columns else end_idx,
                    'duration_minutes': bout_length * self.sample_rate_seconds / 60,
                    'mean_acceleration': float(bout_data['acceleration'].mean()),
                    'max_acceleration': float(bout_data['acceleration'].max()),
                    'sample_count': bout_length
                }
                
                bouts.append(bout)
        
        return bouts
    
    def _analyze_hourly_patterns(self, data: pd.DataFrame) -> Dict:
        """Analyze activity patterns by hour of day."""
        if 'timestamp' not in data.columns:
            return {}
            
        data_copy = data.copy()
        data_copy['hour'] = pd.to_datetime(data_copy['timestamp']).dt.hour
        
        hourly_stats = {}
        
        for hour in range(24):
            hour_data = data_copy[data_copy['hour'] == hour]
            
            if len(hour_data) > 0:
                acc = hour_data['acceleration']
                hourly_stats[hour] = {
                    'sample_count': len(hour_data),
                    'mean_acceleration': float(acc.mean()),
                    'std_acceleration': float(acc.std()),
                    'max_acceleration': float(acc.max()),
                    'sedentary_percentage': float(((acc < self.thresholds['light']).sum() / len(acc)) * 100),
                    'light_percentage': float((((acc >= self.thresholds['light']) & 
                                             (acc < self.thresholds['moderate'])).sum() / len(acc)) * 100),
                    'moderate_percentage': float((((acc >= self.thresholds['moderate']) & 
                                                (acc < self.thresholds['vigorous'])).sum() / len(acc)) * 100),
                    'vigorous_percentage': float(((acc >= self.thresholds['vigorous']).sum() / len(acc)) * 100)
                }
        
        # Find peak activity hours
        if hourly_stats:
            peak_hour = max(hourly_stats.keys(), key=lambda h: hourly_stats[h]['mean_acceleration'])
            lowest_hour = min(hourly_stats.keys(), key=lambda h: hourly_stats[h]['mean_acceleration'])
            
            summary = {
                'hourly_data': hourly_stats,
                'peak_activity_hour': peak_hour,
                'lowest_activity_hour': lowest_hour,
                'peak_activity_value': hourly_stats[peak_hour]['mean_acceleration'],
                'lowest_activity_value': hourly_stats[lowest_hour]['mean_acceleration']
            }
        else:
            summary = {'hourly_data': {}}
            
        return summary
    
    def _analyze_weekly_patterns(self, data: pd.DataFrame) -> Dict:
        """Analyze activity patterns by day of week."""
        if 'timestamp' not in data.columns:
            return {}
            
        data_copy = data.copy()
        data_copy['weekday'] = pd.to_datetime(data_copy['timestamp']).dt.day_name()
        
        weekly_stats = {}
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            day_data = data_copy[data_copy['weekday'] == day]
            
            if len(day_data) > 0:
                acc = day_data['acceleration']
                weekly_stats[day] = {
                    'sample_count': len(day_data),
                    'mean_acceleration': float(acc.mean()),
                    'total_mvpa_minutes': float(((acc >= self.thresholds['moderate']).sum() * 
                                               self.sample_rate_seconds) / 60)
                }
        
        return weekly_stats
    
    def _analyze_activity_transitions(self, classified_data: pd.DataFrame) -> Dict:
        """Analyze transitions between activity intensity levels."""
        transitions = {
            'total_transitions': 0,
            'transition_matrix': {},
            'sedentary_breaks': 0,
            'activity_resumptions': 0
        }
        
        intensity_sequence = classified_data['activity_intensity']
        
        # Count transitions
        for i in range(1, len(intensity_sequence)):
            prev_activity = intensity_sequence.iloc[i-1]
            curr_activity = intensity_sequence.iloc[i]
            
            if prev_activity != curr_activity:
                transitions['total_transitions'] += 1
                
                # Build transition matrix
                key = f"{prev_activity}_to_{curr_activity}"
                transitions['transition_matrix'][key] = transitions['transition_matrix'].get(key, 0) + 1
                
                # Count specific transition types
                if prev_activity == 'sedentary' and curr_activity != 'sedentary':
                    transitions['sedentary_breaks'] += 1
                elif prev_activity != 'sedentary' and curr_activity == 'sedentary':
                    transitions['activity_resumptions'] += 1
        
        # Calculate transition rates (per hour)
        total_time_hours = len(intensity_sequence) * self.sample_rate_seconds / 3600
        if total_time_hours > 0:
            transitions['transitions_per_hour'] = transitions['total_transitions'] / total_time_hours
            transitions['sedentary_breaks_per_hour'] = transitions['sedentary_breaks'] / total_time_hours
        
        return transitions
    
    def _calculate_summary_metrics(self, classified_data: pd.DataFrame, activity_bouts: Dict) -> Dict:
        """Calculate summary metrics for activity analysis."""
        summary = {}
        
        # Overall activity distribution
        intensity_counts = classified_data['activity_intensity'].value_counts()
        total_samples = len(classified_data)
        
        for intensity in ['sedentary', 'light', 'moderate', 'vigorous']:
            count = intensity_counts.get(intensity, 0)
            summary[f'{intensity}_percentage'] = float((count / total_samples) * 100)
            summary[f'{intensity}_minutes'] = float((count * self.sample_rate_seconds) / 60)
        
        # MVPA metrics
        mvpa_samples = intensity_counts.get('moderate', 0) + intensity_counts.get('vigorous', 0)
        summary['mvpa_percentage'] = float((mvpa_samples / total_samples) * 100)
        summary['mvpa_minutes'] = float((mvpa_samples * self.sample_rate_seconds) / 60)
        
        # Bout metrics
        summary['mvpa_bout_count'] = len(activity_bouts.get('mvpa_bouts', []))
        summary['total_mvpa_bout_minutes'] = sum(bout['duration_minutes'] 
                                               for bout in activity_bouts.get('mvpa_bouts', []))
        summary['average_mvpa_bout_duration'] = (summary['total_mvpa_bout_minutes'] / 
                                               summary['mvpa_bout_count'] 
                                               if summary['mvpa_bout_count'] > 0 else 0)
        
        summary['sedentary_bout_count'] = len(activity_bouts.get('sedentary_bouts', []))
        summary['total_sedentary_bout_minutes'] = sum(bout['duration_minutes'] 
                                                    for bout in activity_bouts.get('sedentary_bouts', []))
        summary['average_sedentary_bout_duration'] = (summary['total_sedentary_bout_minutes'] / 
                                                     summary['sedentary_bout_count'] 
                                                     if summary['sedentary_bout_count'] > 0 else 0)
        
        # Activity guidelines compliance
        # WHO guidelines: 150 minutes of moderate-intensity or 75 minutes vigorous-intensity per week
        summary['meets_who_mvpa_guidelines'] = summary['mvpa_minutes'] >= 150 * 7  # Weekly equivalent
        summary['meets_who_bout_guidelines'] = summary['total_mvpa_bout_minutes'] >= 75  # Bout-accumulated MVPA
        
        return summary