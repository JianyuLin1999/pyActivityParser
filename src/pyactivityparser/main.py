"""
Main pyActivityParser Class

The main interface for pyActivityParser accelerometer data analysis.
"""

import os
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

from .data_loader import AccelerometerDataLoader
from .core_analysis import CoreAnalysis
from .quality_assessment import QualityAssessment
from .activity_analysis import ActivityAnalysis
from .sleep_analysis import SleepAnalysis
from .report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PyActivityParser:
    """
    Main pyActivityParser accelerometer data analysis class.
    
    Provides a simplified Python implementation inspired by the GGIR R package
    for processing and analyzing accelerometer data from CSV files.
    """
    
    def __init__(self, data_dir: str = "data", output_dir: str = "output", 
                 sample_rate_seconds: int = 5, verbose: bool = True):
        """
        Initialize pyActivityParser analyzer.
        
        Args:
            data_dir (str): Directory containing input CSV files
            output_dir (str): Directory for output files
            sample_rate_seconds (int): Data sampling interval in seconds
            verbose (bool): Enable verbose logging
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.sample_rate_seconds = sample_rate_seconds
        self.verbose = verbose
        
        # Set logging level
        if not verbose:
            logging.getLogger().setLevel(logging.WARNING)
        
        # Initialize analysis modules
        self.data_loader = AccelerometerDataLoader()
        self.core_analysis = CoreAnalysis(sample_rate_seconds)
        self.quality_assessment = QualityAssessment()
        self.activity_analysis = ActivityAnalysis(sample_rate_seconds)
        self.sleep_analysis = SleepAnalysis(sample_rate_seconds)
        self.report_generator = ReportGenerator(output_dir)
        
        logger.info(f"pyActivityParser initialized - Data: {data_dir}, Output: {output_dir}")
    
    def process_file(self, filename: str) -> Dict:
        """
        Process a single accelerometer data file.
        
        Args:
            filename (str): Name of the CSV file to process
            
        Returns:
            Dict: Complete analysis results
        """
        file_path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Starting analysis of {filename}")
        start_time = datetime.now()
        
        try:
            # Step 1: Load data
            logger.info("Step 1: Loading data...")
            loaded_data = self.data_loader.load_file(file_path)
            participant_id = loaded_data['participant_id']
            metadata = loaded_data['metadata']
            data = loaded_data['data']
            
            # Step 2: Core analysis
            logger.info("Step 2: Core analysis...")
            core_results = self.core_analysis.process_data(data, metadata)
            
            # Get processed data with wear_status column
            processed_data = core_results['processed_data']
            
            # Step 3: Quality assessment
            logger.info("Step 3: Quality assessment...")
            quality_results = self.quality_assessment.assess_quality(processed_data, metadata, core_results)
            
            # Step 4: Activity analysis
            logger.info("Step 4: Activity analysis...")
            activity_results = self.activity_analysis.analyze_activity_patterns(processed_data, core_results)
            
            # Step 5: Sleep analysis
            logger.info("Step 5: Sleep analysis...")
            sleep_results = self.sleep_analysis.analyze_sleep_patterns(processed_data, core_results)
            
            # Compile results
            analysis_results = {
                'data_summary': self.data_loader.get_data_summary(),
                'core_analysis': core_results,
                'quality_assessment': quality_results,
                'activity_analysis': activity_results,
                'sleep_analysis': sleep_results
            }
            
            # Step 6: Generate reports
            logger.info("Step 6: Generating reports...")
            report_results = self.report_generator.generate_comprehensive_report(
                participant_id, analysis_results
            )
            
            processing_time = datetime.now() - start_time
            
            result = {
                'participant_id': participant_id,
                'filename': filename,
                'status': 'success',
                'processing_time_seconds': processing_time.total_seconds(),
                'analysis_results': analysis_results,
                'report_results': report_results
            }
            
            logger.info(f"Analysis completed successfully in {processing_time.total_seconds():.1f} seconds")
            return result
            
        except Exception as e:
            processing_time = datetime.now() - start_time
            error_result = {
                'participant_id': getattr(self.data_loader, 'participant_id', 'unknown'),
                'filename': filename,
                'status': 'error',
                'error': str(e),
                'processing_time_seconds': processing_time.total_seconds()
            }
            
            logger.error(f"Analysis failed: {str(e)}")
            return error_result
    
    def process_directory(self, file_pattern: str = "*.csv") -> List[Dict]:
        """
        Process all CSV files in the data directory.
        
        Args:
            file_pattern (str): File pattern to match (default: "*.csv")
            
        Returns:
            List[Dict]: Results for all processed files
        """
        import glob
        
        # Find CSV files
        csv_files = glob.glob(os.path.join(self.data_dir, file_pattern))
        csv_files = [os.path.basename(f) for f in csv_files]
        
        if not csv_files:
            logger.warning(f"No CSV files found in {self.data_dir}")
            return []
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        results = []
        for i, filename in enumerate(csv_files, 1):
            logger.info(f"Processing file {i}/{len(csv_files)}: {filename}")
            
            try:
                result = self.process_file(filename)
                results.append(result)
                
                # Log progress
                if result['status'] == 'success':
                    logger.info(f"✓ {filename} completed successfully")
                else:
                    logger.warning(f"✗ {filename} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"✗ {filename} failed with exception: {str(e)}")
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Generate batch summary
        logger.info("Generating batch summary...")
        summary_file = self.report_generator.generate_batch_summary(results)
        
        successful = len([r for r in results if r.get('status') == 'success'])
        failed = len(results) - successful
        
        logger.info(f"Batch processing completed: {successful} successful, {failed} failed")
        logger.info(f"Batch summary saved to: {summary_file}")
        
        return results
    
    def get_analysis_summary(self, results: List[Dict]) -> Dict:
        """
        Get summary statistics across multiple analyses.
        
        Args:
            results (List[Dict]): Results from process_directory or multiple process_file calls
            
        Returns:
            Dict: Summary statistics
        """
        successful_results = [r for r in results if r.get('status') == 'success']
        
        if not successful_results:
            return {'error': 'No successful analyses to summarize'}
        
        # Extract key metrics
        quality_scores = []
        wear_times = []
        mvpa_minutes = []
        sleep_hours = []
        
        for result in successful_results:
            analysis = result.get('analysis_results', {})
            
            # Quality scores
            quality_assessment = analysis.get('quality_assessment', {})
            if quality_assessment:
                overall_assessment = quality_assessment.get('overall_assessment', {})
                quality_scores.append(overall_assessment.get('overall_score', 0))
            
            # Activity metrics
            core_analysis = analysis.get('core_analysis', {})
            if core_analysis:
                wear_detection = core_analysis.get('wear_detection', {})
                activity_levels = core_analysis.get('activity_levels', {})
                
                wear_times.append(wear_detection.get('total_wear_time_hours', 0))
                mvpa_minutes.append(activity_levels.get('mvpa_minutes', 0))
            
            # Sleep metrics
            sleep_analysis = analysis.get('sleep_analysis', {})
            if sleep_analysis:
                sleep_summary = sleep_analysis.get('sleep_summary', {})
                sleep_hours.append(sleep_summary.get('total_sleep_time_hours', 0))
        
        import numpy as np
        
        summary = {
            'total_participants': len(results),
            'successful_analyses': len(successful_results),
            'failed_analyses': len(results) - len(successful_results),
            'success_rate': len(successful_results) / len(results) * 100 if results else 0,
            
            'quality_scores': {
                'mean': float(np.mean(quality_scores)) if quality_scores else 0,
                'std': float(np.std(quality_scores)) if quality_scores else 0,
                'min': float(np.min(quality_scores)) if quality_scores else 0,
                'max': float(np.max(quality_scores)) if quality_scores else 0
            },
            
            'wear_time_hours': {
                'mean': float(np.mean(wear_times)) if wear_times else 0,
                'std': float(np.std(wear_times)) if wear_times else 0,
                'min': float(np.min(wear_times)) if wear_times else 0,
                'max': float(np.max(wear_times)) if wear_times else 0
            },
            
            'mvpa_minutes': {
                'mean': float(np.mean(mvpa_minutes)) if mvpa_minutes else 0,
                'std': float(np.std(mvpa_minutes)) if mvpa_minutes else 0,
                'min': float(np.min(mvpa_minutes)) if mvpa_minutes else 0,
                'max': float(np.max(mvpa_minutes)) if mvpa_minutes else 0
            },
            
            'sleep_hours': {
                'mean': float(np.mean(sleep_hours)) if sleep_hours else 0,
                'std': float(np.std(sleep_hours)) if sleep_hours else 0,
                'min': float(np.min(sleep_hours)) if sleep_hours else 0,
                'max': float(np.max(sleep_hours)) if sleep_hours else 0
            }
        }
        
        return summary
    
    def print_summary(self, results: List[Dict]) -> None:
        """Print a formatted summary of analysis results."""
        summary = self.get_analysis_summary(results)
        
        if 'error' in summary:
            print(f"Error: {summary['error']}")
            return
        
        print("\n" + "="*60)
        print("PyActivityParser Analysis Summary")
        print("="*60)
        print(f"Total participants: {summary['total_participants']}")
        print(f"Successful analyses: {summary['successful_analyses']}")
        print(f"Failed analyses: {summary['failed_analyses']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print()
        
        print("Quality Scores:")
        qs = summary['quality_scores']
        print(f"  Mean: {qs['mean']:.1f} ± {qs['std']:.1f}")
        print(f"  Range: {qs['min']:.1f} - {qs['max']:.1f}")
        print()
        
        print("Wear Time (hours):")
        wt = summary['wear_time_hours']
        print(f"  Mean: {wt['mean']:.1f} ± {wt['std']:.1f}")
        print(f"  Range: {wt['min']:.1f} - {wt['max']:.1f}")
        print()
        
        print("MVPA Minutes:")
        mvpa = summary['mvpa_minutes']
        print(f"  Mean: {mvpa['mean']:.1f} ± {mvpa['std']:.1f}")
        print(f"  Range: {mvpa['min']:.1f} - {mvpa['max']:.1f}")
        print()
        
        print("Sleep Hours:")
        sleep = summary['sleep_hours']
        print(f"  Mean: {sleep['mean']:.1f} ± {sleep['std']:.1f}")
        print(f"  Range: {sleep['min']:.1f} - {sleep['max']:.1f}")
        print("="*60)