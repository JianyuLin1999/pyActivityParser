"""
Sleep Analysis Module for PyGGIR

Provides sleep pattern detection and analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SleepAnalysis:
    """
    Sleep pattern detection and analysis.
    
    Inspired by GGIR Parts 3-4: rest period detection and sleep analysis.
    """
    
    def __init__(self, sample_rate_seconds: int = 5):
        self.sample_rate_seconds = sample_rate_seconds
        
        # Sleep detection parameters
        self.sleep_params = {
            'inactivity_threshold_mg': 10,  # Threshold for considering a period as inactive
            'min_rest_period_minutes': 60,  # Minimum duration for a rest period
            'sleep_window_start_hour': 18,  # Earliest possible sleep onset (6 PM)
            'sleep_window_end_hour': 12,    # Latest possible wake time (12 PM next day)
            'min_sleep_duration_hours': 3,  # Minimum sleep duration to consider valid
            'max_sleep_duration_hours': 12  # Maximum sleep duration to consider valid
        }
    
    def analyze_sleep_patterns(self, data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """
        Perform comprehensive sleep pattern analysis.
        
        Args:
            data (pd.DataFrame): Processed accelerometer data
            analysis_results (Dict): Results from core analysis
            
        Returns:
            Dict: Sleep analysis results
        """
        logger.info("Starting sleep pattern analysis")
        
        if 'timestamp' not in data.columns:
            logger.warning("No timestamp column available for sleep analysis")
            return {}
        
        # Detect rest periods
        rest_periods = self._detect_rest_periods(data)
        
        # Identify sleep periods from rest periods
        sleep_periods = self._identify_sleep_periods(rest_periods, data)
        
        # Analyze sleep characteristics
        sleep_characteristics = self._analyze_sleep_characteristics(sleep_periods, data)
        
        # Calculate sleep summary metrics
        sleep_summary = self._calculate_sleep_summary(sleep_periods, sleep_characteristics)
        
        # Analyze sleep regularity
        sleep_regularity = self._analyze_sleep_regularity(sleep_periods)
        
        results = {
            'rest_periods': rest_periods,
            'sleep_periods': sleep_periods,
            'sleep_characteristics': sleep_characteristics,
            'sleep_summary': sleep_summary,
            'sleep_regularity': sleep_regularity
        }
        
        logger.info(f"Sleep analysis completed. Found {len(sleep_periods)} sleep periods")
        return results
    
    def _detect_rest_periods(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect periods of low activity that might indicate rest or sleep.
        
        Uses a simple threshold-based approach.
        """
        # Calculate rolling average to smooth the data
        window_size = max(1, 300 // self.sample_rate_seconds)  # 5-minute rolling window
        data_smooth = data.copy()
        data_smooth['acceleration_smooth'] = data['acceleration'].rolling(
            window=window_size, min_periods=1
        ).mean()
        
        # Identify inactive periods
        inactive_mask = data_smooth['acceleration_smooth'] < self.sleep_params['inactivity_threshold_mg']
        
        # Find continuous inactive periods
        rest_periods = self._find_continuous_periods(inactive_mask, data)
        
        # Filter by minimum duration
        min_samples = int(self.sleep_params['min_rest_period_minutes'] * 60 / self.sample_rate_seconds)
        filtered_periods = [period for period in rest_periods 
                          if period['duration_minutes'] >= self.sleep_params['min_rest_period_minutes']]
        
        logger.info(f"Detected {len(filtered_periods)} rest periods")
        return filtered_periods
    
    def _find_continuous_periods(self, mask: pd.Series, data: pd.DataFrame) -> List[Dict]:
        """Find continuous periods where mask is True."""
        periods = []
        
        if mask.sum() == 0:
            return periods
        
        # Find transitions
        mask_diff = mask.astype(int).diff()
        starts = mask_diff[mask_diff == 1].index
        ends = mask_diff[mask_diff == -1].index
        
        # Handle edge cases
        if mask.iloc[0]:
            starts = [mask.index[0]] + list(starts)
        if mask.iloc[-1]:
            ends = list(ends) + [mask.index[-1]]
        
        for start_idx, end_idx in zip(starts, ends):
            period_data = data.loc[start_idx:end_idx]
            duration_minutes = (end_idx - start_idx + 1) * self.sample_rate_seconds / 60
            
            period = {
                'start_time': period_data['timestamp'].iloc[0],
                'end_time': period_data['timestamp'].iloc[-1],
                'start_index': start_idx,
                'end_index': end_idx,
                'duration_minutes': duration_minutes,
                'mean_acceleration': float(period_data['acceleration'].mean()),
                'min_acceleration': float(period_data['acceleration'].min()),
                'max_acceleration': float(period_data['acceleration'].max())
            }
            
            periods.append(period)
        
        return periods
    
    def _identify_sleep_periods(self, rest_periods: List[Dict], data: pd.DataFrame) -> List[Dict]:
        """
        Identify which rest periods are likely to be sleep periods.
        
        Uses heuristics based on timing and duration.
        """
        sleep_periods = []
        
        for period in rest_periods:
            start_time = pd.to_datetime(period['start_time'])
            end_time = pd.to_datetime(period['end_time'])
            duration_hours = period['duration_minutes'] / 60
            
            # Check if period falls within typical sleep hours and has reasonable duration
            is_sleep = self._is_likely_sleep_period(start_time, end_time, duration_hours)
            
            if is_sleep:
                sleep_period = period.copy()
                sleep_period['sleep_type'] = self._classify_sleep_type(start_time, duration_hours)
                sleep_periods.append(sleep_period)
        
        # Sort by start time
        sleep_periods = sorted(sleep_periods, key=lambda x: x['start_time'])
        
        logger.info(f"Identified {len(sleep_periods)} sleep periods from {len(rest_periods)} rest periods")
        return sleep_periods
    
    def _is_likely_sleep_period(self, start_time: datetime, end_time: datetime, duration_hours: float) -> bool:
        """Determine if a rest period is likely to be sleep."""
        # Check duration constraints
        if (duration_hours < self.sleep_params['min_sleep_duration_hours'] or 
            duration_hours > self.sleep_params['max_sleep_duration_hours']):
            return False
        
        # Check timing - sleep should start in evening/night and end in morning/afternoon
        start_hour = start_time.hour
        end_hour = end_time.hour
        
        # Sleep window: 6 PM to 12 PM next day
        starts_in_evening = start_hour >= self.sleep_params['sleep_window_start_hour'] or start_hour <= 6
        ends_in_morning = end_hour <= self.sleep_params['sleep_window_end_hour']
        
        return starts_in_evening and ends_in_morning
    
    def _classify_sleep_type(self, start_time: datetime, duration_hours: float) -> str:
        """Classify the type of sleep period."""
        start_hour = start_time.hour
        
        if 6 <= start_hour <= 18:  # 6 AM to 6 PM
            if duration_hours <= 2:
                return 'nap'
            else:
                return 'daytime_sleep'
        else:  # Evening/night/early morning
            return 'main_sleep'
    
    def _analyze_sleep_characteristics(self, sleep_periods: List[Dict], data: pd.DataFrame) -> List[Dict]:
        """Analyze detailed characteristics of each sleep period."""
        characteristics = []
        
        for sleep_period in sleep_periods:
            start_idx = sleep_period['start_index']
            end_idx = sleep_period['end_index']
            sleep_data = data.loc[start_idx:end_idx]
            
            # Calculate sleep fragmentation (number of brief awakenings)
            awakening_threshold = 50  # mg - threshold for potential awakening
            awakenings = self._detect_awakenings(sleep_data, awakening_threshold)
            
            # Calculate sleep efficiency (time actually sleeping vs time in bed)
            total_duration = sleep_period['duration_minutes']
            actual_sleep_time = self._estimate_actual_sleep_time(sleep_data)
            sleep_efficiency = (actual_sleep_time / total_duration) * 100 if total_duration > 0 else 0
            
            # Movement during sleep
            movement_stats = {
                'mean_acceleration': float(sleep_data['acceleration'].mean()),
                'std_acceleration': float(sleep_data['acceleration'].std()),
                'movement_variability': float(sleep_data['acceleration'].std() / sleep_data['acceleration'].mean()) 
                                      if sleep_data['acceleration'].mean() > 0 else 0
            }
            
            char = {
                'sleep_period_id': len(characteristics),
                'start_time': sleep_period['start_time'],
                'end_time': sleep_period['end_time'],
                'sleep_type': sleep_period['sleep_type'],
                'total_duration_minutes': total_duration,
                'estimated_sleep_duration_minutes': actual_sleep_time,
                'sleep_efficiency_percentage': sleep_efficiency,
                'awakening_count': len(awakenings),
                'awakening_details': awakenings,
                'movement_during_sleep': movement_stats,
                'sleep_quality_score': self._calculate_sleep_quality_score(
                    sleep_efficiency, len(awakenings), movement_stats['movement_variability']
                )
            }
            
            characteristics.append(char)
        
        return characteristics
    
    def _detect_awakenings(self, sleep_data: pd.DataFrame, threshold: float) -> List[Dict]:
        """Detect potential brief awakenings during sleep."""
        awakening_mask = sleep_data['acceleration'] > threshold
        awakenings = self._find_continuous_periods(awakening_mask, sleep_data)
        
        # Filter awakenings that are at least 1 minute long
        min_awakening_duration = 1  # minutes
        filtered_awakenings = [awk for awk in awakenings 
                             if awk['duration_minutes'] >= min_awakening_duration]
        
        return filtered_awakenings
    
    def _estimate_actual_sleep_time(self, sleep_data: pd.DataFrame) -> float:
        """Estimate actual sleep time by excluding periods of high movement."""
        # Simple approach: exclude periods where acceleration > 20mg
        sleep_threshold = 20  # mg
        actual_sleep_mask = sleep_data['acceleration'] <= sleep_threshold
        actual_sleep_samples = actual_sleep_mask.sum()
        actual_sleep_minutes = actual_sleep_samples * self.sample_rate_seconds / 60
        
        return actual_sleep_minutes
    
    def _calculate_sleep_quality_score(self, efficiency: float, awakening_count: int, 
                                     movement_variability: float) -> float:
        """Calculate a sleep quality score (0-100)."""
        # Start with efficiency score
        quality_score = efficiency
        
        # Penalize for frequent awakenings
        awakening_penalty = min(20, awakening_count * 2)
        quality_score -= awakening_penalty
        
        # Penalize for high movement variability
        movement_penalty = min(10, movement_variability * 10)
        quality_score -= movement_penalty
        
        return max(0, min(100, quality_score))
    
    def _calculate_sleep_summary(self, sleep_periods: List[Dict], 
                               sleep_characteristics: List[Dict]) -> Dict:
        """Calculate overall sleep summary metrics."""
        if not sleep_periods:
            return {}
        
        main_sleep_periods = [char for char in sleep_characteristics 
                            if char['sleep_type'] == 'main_sleep']
        nap_periods = [char for char in sleep_characteristics 
                      if char['sleep_type'] == 'nap']
        
        summary = {
            'total_sleep_periods': len(sleep_periods),
            'main_sleep_periods': len(main_sleep_periods),
            'nap_periods': len(nap_periods),
            'total_sleep_time_hours': sum(char['estimated_sleep_duration_minutes'] 
                                        for char in sleep_characteristics) / 60,
            'main_sleep_time_hours': sum(char['estimated_sleep_duration_minutes'] 
                                       for char in main_sleep_periods) / 60,
            'nap_time_hours': sum(char['estimated_sleep_duration_minutes'] 
                                for char in nap_periods) / 60
        }
        
        if main_sleep_periods:
            summary.update({
                'average_sleep_duration_hours': np.mean([char['estimated_sleep_duration_minutes'] 
                                                       for char in main_sleep_periods]) / 60,
                'average_sleep_efficiency': np.mean([char['sleep_efficiency_percentage'] 
                                                   for char in main_sleep_periods]),
                'average_awakening_count': np.mean([char['awakening_count'] 
                                                  for char in main_sleep_periods]),
                'average_sleep_quality_score': np.mean([char['sleep_quality_score'] 
                                                      for char in main_sleep_periods])
            })
        
        return summary
    
    def _analyze_sleep_regularity(self, sleep_periods: List[Dict]) -> Dict:
        """Analyze sleep timing regularity."""
        main_sleep_periods = [period for period in sleep_periods 
                            if period.get('sleep_type') == 'main_sleep']
        
        if len(main_sleep_periods) < 2:
            return {'insufficient_data': True}
        
        # Extract sleep onset and wake times
        sleep_onsets = [pd.to_datetime(period['start_time']).hour + 
                       pd.to_datetime(period['start_time']).minute / 60 
                       for period in main_sleep_periods]
        
        wake_times = [pd.to_datetime(period['end_time']).hour + 
                     pd.to_datetime(period['end_time']).minute / 60 
                     for period in main_sleep_periods]
        
        # Handle times that cross midnight
        sleep_onsets = [time if time <= 12 else time - 24 for time in sleep_onsets]
        
        regularity = {
            'sleep_onset_variability_hours': float(np.std(sleep_onsets)),
            'wake_time_variability_hours': float(np.std(wake_times)),
            'average_sleep_onset_hour': float(np.mean(sleep_onsets)) % 24,
            'average_wake_time_hour': float(np.mean(wake_times)),
            'sleep_regularity_index': self._calculate_sleep_regularity_index(
                sleep_onsets, wake_times
            )
        }
        
        return regularity
    
    def _calculate_sleep_regularity_index(self, sleep_onsets: List[float], 
                                        wake_times: List[float]) -> float:
        """
        Calculate a sleep regularity index (0-100).
        
        Higher scores indicate more regular sleep patterns.
        """
        if len(sleep_onsets) < 2:
            return 0
        
        # Calculate coefficient of variation for both onset and wake times
        onset_cv = np.std(sleep_onsets) / np.mean(sleep_onsets) if np.mean(sleep_onsets) != 0 else 0
        wake_cv = np.std(wake_times) / np.mean(wake_times) if np.mean(wake_times) != 0 else 0
        
        # Combine into a regularity score (lower CV = higher regularity)
        avg_cv = (onset_cv + wake_cv) / 2
        regularity_index = max(0, 100 - (avg_cv * 100))
        
        return float(regularity_index)