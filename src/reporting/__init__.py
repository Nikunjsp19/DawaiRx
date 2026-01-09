"""Reporting module for generating outputs"""

from src.reporting.excel import create_audit_report

try:
    from src.reporting.pdf import create_detailed_pdf_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    create_detailed_pdf_report = None

__all__ = [
    "create_audit_report",
]

if PDF_AVAILABLE:
    __all__.append("create_detailed_pdf_report")
