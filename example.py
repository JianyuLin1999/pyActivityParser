#!/usr/bin/env python3
"""
PyGGIR Example Usage Script

Demonstrates how to use PyGGIR for accelerometer data analysis.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyggir import PyGGIR


def main():
    """Main example function."""
    print("PyGGIR - Python Accelerometer Data Analysis")
    print("=" * 50)
    
    # Initialize PyGGIR
    analyzer = PyGGIR(
        data_dir="data",           # Directory containing CSV files
        output_dir="output",       # Directory for results
        sample_rate_seconds=5,     # 5-second sampling rate
        verbose=True               # Enable detailed logging
    )
    
    print(f"Initialized PyGGIR analyzer")
    print(f"Data directory: {analyzer.data_dir}")
    print(f"Output directory: {analyzer.output_dir}")
    print()
    
    # Example 1: Process a single file
    print("Example 1: Processing single file")
    print("-" * 30)
    
    try:
        # Process the first CSV file
        result = analyzer.process_file("1067459_90004_0_0.csv")
        
        if result['status'] == 'success':
            print(f"✓ Successfully processed {result['filename']}")
            print(f"  Participant ID: {result['participant_id']}")
            print(f"  Processing time: {result['processing_time_seconds']:.1f} seconds")
            
            # Display key results
            analysis = result['analysis_results']
            
            # Data summary
            data_summary = analysis['data_summary']
            print(f"  Data completeness: {data_summary.get('data_completeness', 0)*100:.1f}%")
            
            # Quality assessment
            quality = analysis['quality_assessment']['overall_assessment']
            print(f"  Quality score: {quality['overall_score']:.1f}/100 (Grade: {quality['quality_grade']})")
            
            # Activity summary
            activity_levels = analysis['core_analysis']['activity_levels']
            print(f"  MVPA minutes: {activity_levels.get('mvpa_minutes', 0):.1f}")
            print(f"  Estimated daily steps: {activity_levels.get('average_daily_steps_estimate', 0):.0f}")
            
            # Sleep summary
            sleep_summary = analysis['sleep_analysis'].get('sleep_summary', {})
            if sleep_summary:
                print(f"  Sleep time: {sleep_summary.get('total_sleep_time_hours', 0):.1f} hours")
                print(f"  Sleep efficiency: {sleep_summary.get('average_sleep_efficiency', 0):.1f}%")
        else:
            print(f"✗ Failed to process {result['filename']}: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"✗ Error processing single file: {str(e)}")
    
    print()
    
    # Example 2: Process all files in directory
    print("Example 2: Processing all files in directory")
    print("-" * 40)
    
    try:
        # Process all CSV files
        results = analyzer.process_directory("*.csv")
        
        print(f"Processed {len(results)} files")
        
        # Display summary
        analyzer.print_summary(results)
        
        # Show individual results
        print("\nIndividual Results:")
        for result in results:
            status_symbol = "✓" if result['status'] == 'success' else "✗"
            print(f"  {status_symbol} {result['filename']} - {result['status']}")
            
    except Exception as e:
        print(f"✗ Error processing directory: {str(e)}")
    
    print()
    print("Analysis completed!")
    print(f"Check the '{analyzer.output_dir}' directory for detailed reports and data exports.")


if __name__ == "__main__":
    main()