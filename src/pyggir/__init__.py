"""
PyGGIR - Python Accelerometer Data Analysis Package

A simplified Python implementation inspired by the GGIR R package
for processing and analyzing accelerometer data.
"""

__version__ = "0.1.0"
__author__ = "PyGGIR Development Team"

from .main import PyGGIR
from .data_loader import AccelerometerDataLoader
from .core_analysis import CoreAnalysis
from .quality_assessment import QualityAssessment
from .activity_analysis import ActivityAnalysis
from .sleep_analysis import SleepAnalysis
from .report_generator import ReportGenerator

__all__ = [
    "PyGGIR",
    "AccelerometerDataLoader", 
    "CoreAnalysis",
    "QualityAssessment",
    "ActivityAnalysis",
    "SleepAnalysis",
    "ReportGenerator"
]