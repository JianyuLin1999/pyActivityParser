"""
Data Loader Module for PyGGIR

Handles loading and parsing of accelerometer data from CSV files.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from typing import Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AccelerometerDataLoader:
    """
    Load and parse accelerometer data from CSV files.
    
    Supports CSV files with format:
    Header: acceleration (mg) - StartTime - EndTime - sampleRate = X seconds,imputed
    Data: acceleration_value,imputation_flag
    """
    
    def __init__(self):
        self.metadata = {}
        self.data = None
        self.participant_id = None
        
    def load_file(self, file_path: str) -> Dict:
        """
        Load accelerometer data from CSV file.
        
        Args:
            file_path (str): Path to the CSV file
            
        Returns:
            Dict: Processed data and metadata
        """
        logger.info(f"Loading file: {file_path}")
        
        # Extract participant ID from filename
        self.participant_id = self._extract_participant_id(file_path)
        
        # Read and parse the file
        with open(file_path, 'r') as f:
            header_line = f.readline().strip()
            
        # Parse header metadata
        self.metadata = self._parse_header(header_line)
        
        # Load data
        self.data = pd.read_csv(file_path, skiprows=1, header=None, 
                               names=['acceleration', 'imputed'])
        
        # Add timestamp column
        self.data = self._add_timestamps()
        
        # Validate data
        self._validate_data()
        
        logger.info(f"Loaded {len(self.data)} data points for participant {self.participant_id}")
        
        return {
            'participant_id': self.participant_id,
            'metadata': self.metadata,
            'data': self.data
        }
    
    def _extract_participant_id(self, file_path: str) -> str:
        """Extract participant ID from filename."""
        filename = file_path.split('/')[-1]
        # Extract first part before underscore as participant ID
        participant_id = filename.split('_')[0]
        return participant_id
    
    def _parse_header(self, header_line: str) -> Dict:
        """
        Parse header line to extract metadata.
        
        Expected format: 
        acceleration (mg) - 2015-08-06 10:00:00 - 2015-08-13 09:59:55 - sampleRate = 5 seconds,imputed
        """
        metadata = {}
        
        # Extract data type and unit
        unit_match = re.search(r'acceleration \((\w+)\)', header_line)
        metadata['unit'] = unit_match.group(1) if unit_match else 'mg'
        
        # Extract time range
        time_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        time_match = re.search(time_pattern, header_line)
        
        if time_match:
            start_time_str = time_match.group(1)
            end_time_str = time_match.group(2)
            metadata['start_time'] = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            metadata['end_time'] = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        
        # Extract sample rate
        sample_rate_match = re.search(r'sampleRate = (\d+) seconds', header_line)
        metadata['sample_rate_seconds'] = int(sample_rate_match.group(1)) if sample_rate_match else 5
        
        # Check if data is imputed
        metadata['has_imputed_data'] = 'imputed' in header_line.lower()
        
        # Calculate expected number of samples
        if 'start_time' in metadata and 'end_time' in metadata:
            duration = metadata['end_time'] - metadata['start_time']
            expected_samples = int(duration.total_seconds() / metadata['sample_rate_seconds'])
            metadata['expected_samples'] = expected_samples
        
        return metadata
    
    def _add_timestamps(self) -> pd.DataFrame:
        """Add timestamp column to the data."""
        data_copy = self.data.copy()
        
        if 'start_time' in self.metadata:
            start_time = self.metadata['start_time']
            sample_rate = self.metadata['sample_rate_seconds']
            
            # Generate timestamps
            timestamps = [start_time + timedelta(seconds=i * sample_rate) 
                         for i in range(len(data_copy))]
            data_copy['timestamp'] = timestamps
            
            # Reorder columns
            data_copy = data_copy[['timestamp', 'acceleration', 'imputed']]
        
        return data_copy
    
    def _validate_data(self) -> None:
        """Validate loaded data for quality and consistency."""
        validation_results = {
            'total_samples': len(self.data),
            'missing_values': self.data['acceleration'].isna().sum(),
            'imputed_samples': self.data['imputed'].sum(),
            'acceleration_range': {
                'min': self.data['acceleration'].min(),
                'max': self.data['acceleration'].max(),
                'mean': self.data['acceleration'].mean(),
                'std': self.data['acceleration'].std()
            }
        }
        
        # Check for expected sample count
        if 'expected_samples' in self.metadata:
            expected = self.metadata['expected_samples']
            actual = len(self.data)
            validation_results['sample_count_match'] = abs(expected - actual) <= 1
            
        self.metadata['validation'] = validation_results
        
        # Log validation results
        logger.info(f"Data validation: {validation_results['total_samples']} samples, "
                   f"{validation_results['imputed_samples']} imputed, "
                   f"{validation_results['missing_values']} missing")
    
    def get_data_summary(self) -> Dict:
        """Get a summary of the loaded data."""
        if self.data is None:
            return {}
            
        summary = {
            'participant_id': self.participant_id,
            'start_time': self.metadata.get('start_time'),
            'end_time': self.metadata.get('end_time'),
            'sample_rate_seconds': self.metadata.get('sample_rate_seconds'),
            'total_samples': len(self.data),
            'imputed_samples': self.data['imputed'].sum(),
            'data_completeness': 1 - (self.data['acceleration'].isna().sum() / len(self.data)),
            'acceleration_stats': {
                'mean': float(self.data['acceleration'].mean()),
                'std': float(self.data['acceleration'].std()),
                'min': float(self.data['acceleration'].min()),
                'max': float(self.data['acceleration'].max()),
                'median': float(self.data['acceleration'].median())
            }
        }
        
        return summary