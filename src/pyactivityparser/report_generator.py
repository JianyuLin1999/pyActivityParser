"""
Report Generator Module for PyActivityParser

Generates comprehensive analysis reports in various formats.
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate comprehensive analysis reports.
    
    Inspired by ActivityParser's reporting functionality across all parts.
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """Ensure output directory exists."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "data"), exist_ok=True)
    
    def generate_comprehensive_report(self, participant_id: str, analysis_results: Dict) -> Dict:
        """
        Generate a comprehensive analysis report for a participant.
        
        Args:
            participant_id (str): Participant identifier
            analysis_results (Dict): Complete analysis results
            
        Returns:
            Dict: Report generation results with file paths
        """
        logger.info(f"Generating comprehensive report for participant {participant_id}")
        
        report_timestamp = datetime.now()
        
        # Generate different report formats
        report_files = {}
        
        # 1. JSON summary report
        json_report = self._generate_json_report(participant_id, analysis_results, report_timestamp)
        json_file = os.path.join(self.output_dir, "reports", f"{participant_id}_summary.json")
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2, default=str)
        report_files['json_summary'] = json_file
        
        # 2. CSV data exports
        csv_files = self._generate_csv_exports(participant_id, analysis_results)
        report_files.update(csv_files)
        
        # 3. Text summary report
        text_report = self._generate_text_summary(participant_id, analysis_results, report_timestamp)
        text_file = os.path.join(self.output_dir, "reports", f"{participant_id}_summary.txt")
        with open(text_file, 'w') as f:
            f.write(text_report)
        report_files['text_summary'] = text_file
        
        logger.info(f"Report generation completed. Files: {list(report_files.keys())}")
        
        return {
            'participant_id': participant_id,
            'report_timestamp': report_timestamp,
            'files_generated': report_files,
            'summary': self._extract_key_findings(analysis_results)
        }
    
    def _generate_json_report(self, participant_id: str, analysis_results: Dict, 
                            timestamp: datetime) -> Dict:
        """Generate comprehensive JSON report."""
        return {
            'report_info': {
                'participant_id': participant_id,
                'generated_at': timestamp,
                'pyactivityparser_version': '0.1.0',
                'analysis_type': 'comprehensive_accelerometer_analysis'
            },
            'data_summary': analysis_results.get('data_summary', {}),
            'quality_assessment': analysis_results.get('quality_assessment', {}),
            'core_analysis': {
                'basic_metrics': analysis_results.get('core_analysis', {}).get('basic_metrics', {}),
                'wear_detection': analysis_results.get('core_analysis', {}).get('wear_detection', {}),
                'activity_levels': analysis_results.get('core_analysis', {}).get('activity_levels', {}),
                'quality_metrics': analysis_results.get('core_analysis', {}).get('quality_metrics', {})
            },
            'activity_analysis': analysis_results.get('activity_analysis', {}),
            'sleep_analysis': analysis_results.get('sleep_analysis', {}),
            'key_findings': self._extract_key_findings(analysis_results)
        }
    
    def _generate_csv_exports(self, participant_id: str, analysis_results: Dict) -> Dict:
        """Generate CSV data exports."""
        csv_files = {}
        
        # 1. Daily summary CSV
        daily_summaries = analysis_results.get('core_analysis', {}).get('daily_summaries', [])
        if daily_summaries:
            daily_df = pd.DataFrame(daily_summaries)
            daily_df['participant_id'] = participant_id
            daily_file = os.path.join(self.output_dir, "data", f"{participant_id}_daily_summary.csv")
            daily_df.to_csv(daily_file, index=False)
            csv_files['daily_summary'] = daily_file
        
        # 2. Sleep periods CSV
        sleep_periods = analysis_results.get('sleep_analysis', {}).get('sleep_characteristics', [])
        if sleep_periods:
            sleep_df = pd.DataFrame(sleep_periods)
            sleep_df['participant_id'] = participant_id
            sleep_file = os.path.join(self.output_dir, "data", f"{participant_id}_sleep_periods.csv")
            sleep_df.to_csv(sleep_file, index=False)
            csv_files['sleep_periods'] = sleep_file
        
        # 3. Activity bouts CSV
        activity_analysis = analysis_results.get('activity_analysis', {})
        if 'activity_bouts' in activity_analysis:
            bouts_data = []
            for bout_type, bouts in activity_analysis['activity_bouts'].items():
                for bout in bouts:
                    bout_record = bout.copy()
                    bout_record['participant_id'] = participant_id
                    bout_record['bout_type'] = bout_type
                    bouts_data.append(bout_record)
            
            if bouts_data:
                bouts_df = pd.DataFrame(bouts_data)
                bouts_file = os.path.join(self.output_dir, "data", f"{participant_id}_activity_bouts.csv")
                bouts_df.to_csv(bouts_file, index=False)
                csv_files['activity_bouts'] = bouts_file
        
        # 4. Hourly patterns CSV
        hourly_patterns = activity_analysis.get('hourly_patterns', {}).get('hourly_data', {})
        if hourly_patterns:
            hourly_data = []
            for hour, stats in hourly_patterns.items():
                record = stats.copy()
                record['participant_id'] = participant_id
                record['hour'] = hour
                hourly_data.append(record)
            
            hourly_df = pd.DataFrame(hourly_data)
            hourly_file = os.path.join(self.output_dir, "data", f"{participant_id}_hourly_patterns.csv")
            hourly_df.to_csv(hourly_file, index=False)
            csv_files['hourly_patterns'] = hourly_file
        
        return csv_files
    
    def _generate_text_summary(self, participant_id: str, analysis_results: Dict, 
                             timestamp: datetime) -> str:
        """Generate human-readable text summary."""
        
        # Extract key data
        data_summary = analysis_results.get('data_summary', {})
        quality_assessment = analysis_results.get('quality_assessment', {})
        core_analysis = analysis_results.get('core_analysis', {})
        activity_analysis = analysis_results.get('activity_analysis', {})
        sleep_analysis = analysis_results.get('sleep_analysis', {})
        
        report_lines = [
            "="*80,
            f"PyActivityParser Accelerometer Data Analysis Report",
            f"Participant ID: {participant_id}",
            f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "="*80,
            "",
            "DATA OVERVIEW",
            "-"*40,
            f"Recording period: {data_summary.get('start_time', 'N/A')} to {data_summary.get('end_time', 'N/A')}",
            f"Sample rate: {data_summary.get('sample_rate_seconds', 'N/A')} seconds",
            f"Total samples: {data_summary.get('total_samples', 'N/A'):,}",
            f"Data completeness: {data_summary.get('data_completeness', 0)*100:.1f}%",
            f"Imputed samples: {data_summary.get('imputed_samples', 'N/A'):,}",
            "",
        ]
        
        # Quality Assessment
        if quality_assessment:
            overall_assessment = quality_assessment.get('overall_assessment', {})
            report_lines.extend([
                "QUALITY ASSESSMENT",
                "-"*40,
                f"Overall quality score: {overall_assessment.get('overall_score', 'N/A')}/100 (Grade: {overall_assessment.get('quality_grade', 'N/A')})",
                f"Data usable for analysis: {'Yes' if overall_assessment.get('data_usable', False) else 'No'}",
                "",
                "Quality Scores:",
                f"  Data completeness: {overall_assessment.get('individual_scores', {}).get('data_completeness', 'N/A'):.1f}/100",
                f"  Wear compliance: {overall_assessment.get('individual_scores', {}).get('wear_compliance', 'N/A'):.1f}/100",
                f"  Data integrity: {overall_assessment.get('individual_scores', {}).get('data_integrity', 'N/A'):.1f}/100",
                f"  Activity patterns: {overall_assessment.get('individual_scores', {}).get('activity_patterns', 'N/A'):.1f}/100",
                "",
            ])
            
            # Recommendations
            recommendations = quality_assessment.get('recommendations', [])
            if recommendations:
                report_lines.extend([
                    "Recommendations:",
                    *[f"  • {rec}" for rec in recommendations],
                    "",
                ])
        
        # Wear Time Analysis
        wear_detection = core_analysis.get('wear_detection', {})
        if wear_detection:
            report_lines.extend([
                "WEAR TIME ANALYSIS",
                "-"*40,
                f"Total wear time: {wear_detection.get('total_wear_time_hours', 0):.1f} hours",
                f"Wear compliance: {wear_detection.get('wear_percentage', 0):.1f}%",
                f"Non-wear periods: {len(wear_detection.get('non_wear_periods', []))}",
                "",
            ])
        
        # Activity Analysis
        activity_levels = core_analysis.get('activity_levels', {})
        if activity_levels:
            report_lines.extend([
                "ACTIVITY ANALYSIS",
                "-"*40,
                f"Sedentary time: {activity_levels.get('sedentary_percentage', 0):.1f}%",
                f"Light activity: {activity_levels.get('light_activity_percentage', 0):.1f}%",
                f"Moderate activity: {activity_levels.get('moderate_activity_percentage', 0):.1f}%",
                f"Vigorous activity: {activity_levels.get('high_activity_percentage', 0):.1f}%",
                f"MVPA minutes: {activity_levels.get('mvpa_minutes', 0):.1f}",
                f"Estimated daily steps: {activity_levels.get('average_daily_steps_estimate', 0):.0f}",
                "",
            ])
        
        # Activity Bouts
        if activity_analysis and 'summary_metrics' in activity_analysis:
            summary = activity_analysis['summary_metrics']
            report_lines.extend([
                "ACTIVITY BOUTS",
                "-"*40,
                f"MVPA bouts: {summary.get('mvpa_bout_count', 0)}",
                f"Total MVPA bout time: {summary.get('total_mvpa_bout_minutes', 0):.1f} minutes",
                f"Average MVPA bout duration: {summary.get('average_mvpa_bout_duration', 0):.1f} minutes",
                f"Meets WHO MVPA guidelines: {'Yes' if summary.get('meets_who_mvpa_guidelines', False) else 'No'}",
                "",
            ])
        
        # Sleep Analysis
        sleep_summary = sleep_analysis.get('sleep_summary', {})
        if sleep_summary:
            report_lines.extend([
                "SLEEP ANALYSIS",
                "-"*40,
                f"Total sleep periods: {sleep_summary.get('total_sleep_periods', 0)}",
                f"Main sleep periods: {sleep_summary.get('main_sleep_periods', 0)}",
                f"Total sleep time: {sleep_summary.get('total_sleep_time_hours', 0):.1f} hours",
                f"Average sleep duration: {sleep_summary.get('average_sleep_duration_hours', 0):.1f} hours",
                f"Average sleep efficiency: {sleep_summary.get('average_sleep_efficiency', 0):.1f}%",
                f"Average sleep quality: {sleep_summary.get('average_sleep_quality_score', 0):.1f}/100",
                "",
            ])
        
        # Sleep Regularity
        sleep_regularity = sleep_analysis.get('sleep_regularity', {})
        if sleep_regularity and not sleep_regularity.get('insufficient_data', False):
            report_lines.extend([
                "SLEEP REGULARITY",
                "-"*40,
                f"Sleep onset variability: {sleep_regularity.get('sleep_onset_variability_hours', 0):.1f} hours",
                f"Wake time variability: {sleep_regularity.get('wake_time_variability_hours', 0):.1f} hours",
                f"Sleep regularity index: {sleep_regularity.get('sleep_regularity_index', 0):.1f}/100",
                "",
            ])
        
        # Key Findings
        key_findings = self._extract_key_findings(analysis_results)
        if key_findings:
            report_lines.extend([
                "KEY FINDINGS",
                "-"*40,
                *[f"• {finding}" for finding in key_findings],
                "",
            ])
        
        report_lines.extend([
            "="*80,
            "End of Report",
            "="*80
        ])
        
        return "\n".join(report_lines)
    
    def _extract_key_findings(self, analysis_results: Dict) -> List[str]:
        """Extract key findings from analysis results."""
        findings = []
        
        # Quality findings
        quality_assessment = analysis_results.get('quality_assessment', {})
        if quality_assessment:
            overall_score = quality_assessment.get('overall_assessment', {}).get('overall_score', 0)
            if overall_score >= 90:
                findings.append("Excellent data quality detected")
            elif overall_score < 60:
                findings.append("Poor data quality detected - consider data exclusion")
        
        # Activity findings
        activity_levels = analysis_results.get('core_analysis', {}).get('activity_levels', {})
        if activity_levels:
            sedentary_pct = activity_levels.get('sedentary_percentage', 0)
            mvpa_minutes = activity_levels.get('mvpa_minutes', 0)
            
            if sedentary_pct > 90:
                findings.append("Very high sedentary behavior detected")
            if mvpa_minutes < 150 * 7:  # WHO guidelines
                findings.append("Below recommended MVPA levels")
            if mvpa_minutes > 300 * 7:
                findings.append("Very high activity levels detected")
        
        # Activity bout findings
        activity_analysis = analysis_results.get('activity_analysis', {})
        if activity_analysis and 'summary_metrics' in activity_analysis:
            summary = activity_analysis['summary_metrics']
            if summary.get('meets_who_mvpa_guidelines', False):
                findings.append("Meets WHO physical activity guidelines")
            if summary.get('mvpa_bout_count', 0) == 0:
                findings.append("No sustained MVPA bouts detected")
        
        # Sleep findings
        sleep_summary = analysis_results.get('sleep_analysis', {}).get('sleep_summary', {})
        if sleep_summary:
            avg_sleep_duration = sleep_summary.get('average_sleep_duration_hours', 0)
            avg_sleep_efficiency = sleep_summary.get('average_sleep_efficiency', 0)
            
            if avg_sleep_duration < 6:
                findings.append("Short sleep duration detected")
            elif avg_sleep_duration > 9:
                findings.append("Long sleep duration detected")
            
            if avg_sleep_efficiency < 85:
                findings.append("Poor sleep efficiency detected")
            elif avg_sleep_efficiency > 95:
                findings.append("Excellent sleep efficiency detected")
        
        # Sleep regularity findings
        sleep_regularity = analysis_results.get('sleep_analysis', {}).get('sleep_regularity', {})
        if sleep_regularity and not sleep_regularity.get('insufficient_data', False):
            regularity_index = sleep_regularity.get('sleep_regularity_index', 0)
            if regularity_index > 80:
                findings.append("Highly regular sleep pattern")
            elif regularity_index < 50:
                findings.append("Irregular sleep pattern detected")
        
        return findings
    
    def generate_batch_summary(self, batch_results: List[Dict]) -> str:
        """Generate summary report for multiple participants."""
        logger.info(f"Generating batch summary for {len(batch_results)} participants")
        
        summary_file = os.path.join(self.output_dir, "batch_summary.csv")
        
        # Extract key metrics for each participant
        summary_data = []
        for result in batch_results:
            participant_data = {
                'participant_id': result.get('participant_id', 'unknown'),
                'processing_status': result.get('status', 'unknown'),
                'quality_score': 0,
                'wear_time_hours': 0,
                'mvpa_minutes': 0,
                'sleep_hours': 0,
                'sleep_efficiency': 0
            }
            
            if result.get('status') == 'success':
                analysis_results = result.get('analysis_results', {})
                
                # Quality score
                quality_assessment = analysis_results.get('quality_assessment', {})
                if quality_assessment:
                    participant_data['quality_score'] = quality_assessment.get('overall_assessment', {}).get('overall_score', 0)
                
                # Activity metrics
                core_analysis = analysis_results.get('core_analysis', {})
                if core_analysis:
                    wear_detection = core_analysis.get('wear_detection', {})
                    activity_levels = core_analysis.get('activity_levels', {})
                    
                    participant_data['wear_time_hours'] = wear_detection.get('total_wear_time_hours', 0)
                    participant_data['mvpa_minutes'] = activity_levels.get('mvpa_minutes', 0)
                
                # Sleep metrics
                sleep_analysis = analysis_results.get('sleep_analysis', {})
                if sleep_analysis:
                    sleep_summary = sleep_analysis.get('sleep_summary', {})
                    participant_data['sleep_hours'] = sleep_summary.get('total_sleep_time_hours', 0)
                    participant_data['sleep_efficiency'] = sleep_summary.get('average_sleep_efficiency', 0)
            
            summary_data.append(participant_data)
        
        # Save summary
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(summary_file, index=False)
        
        logger.info(f"Batch summary saved to {summary_file}")
        return summary_file