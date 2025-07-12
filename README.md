# pyActivityParser - Python Accelerometer Data Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A simplified Python implementation inspired by the GGIR R package for processing and analyzing accelerometer data.

## Overview

pyActivityParser is designed to process multi-day accelerometer data for physical activity, sleep, and circadian rhythm research. It provides a comprehensive analysis pipeline that includes data quality assessment, activity pattern detection, sleep analysis, and detailed reporting.

## Key Features

- **Multi-format Support**: Process CSV accelerometer data with flexible input formats
- **Comprehensive Analysis**: 
  - Data quality assessment and validation
  - Wear/non-wear time detection
  - Physical activity intensity classification
  - Sleep pattern detection and analysis
  - Circadian rhythm assessment
- **Detailed Reporting**: Generate JSON, CSV, and text reports
- **Modular Design**: Six-stage processing pipeline inspired by ActivityParser
- **Easy to Use**: Simple API with minimal configuration required

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pyActivityParser.git
cd pyActivityParser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

## Quick Start

### Basic Usage

```python
from pyactivityparser import PyActivityParser

# Initialize analyzer
analyzer = PyActivityParser(
    data_dir="data",           # Directory with CSV files
    output_dir="output",       # Output directory
    sample_rate_seconds=5,     # Data sampling rate
    verbose=True               # Enable detailed logging
)

# Process a single file
result = analyzer.process_file("participant_001.csv")

# Process all files in directory
results = analyzer.process_directory("*.csv")

# Display summary
analyzer.print_summary(results)
```

### Command Line Usage

```bash
# Run the example script
python example.py
```

## Data Format

pyActivityParser supports CSV files with the following format:

**Header line:**
```
acceleration (mg) - 2015-08-06 10:00:00 - 2015-08-13 09:59:55 - sampleRate = 5 seconds,imputed
```

**Data rows:**
```
acceleration_value,imputation_flag
12.5,0
15.8,0
0.0,1
```

Where:
- `acceleration_value`: Acceleration magnitude in milligravity (mg)
- `imputation_flag`: 0 = original data, 1 = imputed data

## Analysis Pipeline

pyActivityParser follows a six-stage analysis pipeline:

1. **Data Loading**: Parse CSV files and extract metadata
2. **Core Analysis**: Calculate basic metrics and detect wear periods
3. **Quality Assessment**: Evaluate data quality and compliance
4. **Activity Analysis**: Classify activity intensities and detect bouts
5. **Sleep Analysis**: Identify sleep periods and calculate sleep metrics
6. **Report Generation**: Create comprehensive analysis reports

## Output Files

### Reports Directory
- `{participant_id}_summary.json`: Comprehensive JSON report
- `{participant_id}_summary.txt`: Human-readable text summary

### Data Directory
- `{participant_id}_daily_summary.csv`: Daily activity summaries
- `{participant_id}_sleep_periods.csv`: Detected sleep periods
- `{participant_id}_activity_bouts.csv`: Physical activity bouts
- `{participant_id}_hourly_patterns.csv`: Hourly activity patterns

### Batch Analysis
- `batch_summary.csv`: Summary metrics for all participants

## Example Results

For a typical 7-day recording, pyActivityParser provides:

- **Data Quality Score**: 0-100 scale with grade (A-F)
- **Wear Time**: Total hours of valid data
- **Activity Metrics**: 
  - Sedentary, light, moderate, vigorous activity percentages
  - MVPA (Moderate-to-Vigorous Physical Activity) minutes
  - Estimated daily steps
- **Sleep Metrics**:
  - Sleep duration and efficiency
  - Sleep onset and wake times
  - Sleep regularity index

## Requirements

- Python 3.7+
- pandas >= 1.3.0
- numpy >= 1.20.0
- matplotlib >= 3.3.0
- scipy >= 1.7.0

## Project Structure

```
pyActivityParser/
├── src/pyactivityparser/    # Core Python package
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Main pyActivityParser class
│   ├── data_loader.py      # Data loading and parsing
│   ├── core_analysis.py    # Core analysis functions
│   ├── quality_assessment.py # Data quality evaluation
│   ├── activity_analysis.py  # Activity pattern analysis
│   ├── sleep_analysis.py     # Sleep detection and analysis
│   └── report_generator.py   # Report generation
├── data/                    # Sample input data
├── output/                  # Analysis results
├── example.py              # Usage examples
├── requirements.txt        # Python dependencies
├── setup.py               # Package installation
└── README.md              # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use pyActivityParser in your research, please cite:

```
pyActivityParser: A Python Implementation for Accelerometer Data Analysis
[Your details here]
```

## Acknowledgments

- Inspired by the [GGIR R package](https://cran.r-project.org/package=GGIR)
- Built for the accelerometer research community

## Support

For questions and support:
- Open an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the example scripts for usage patterns