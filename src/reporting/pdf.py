"""PDF report generation with detailed reporting"""

from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
import logging

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab not installed - PDF generation disabled")

logger = logging.getLogger(__name__)


def create_detailed_pdf_report(
    output_path: str,
    reconciled_df: pd.DataFrame,
    issues_df: pd.DataFrame,
    summary: Dict[str, Any],
    ordered_df: pd.DataFrame = None,
    sold_df: pd.DataFrame = None
):
    """
    Create a detailed PDF audit report similar to BatchRx.
    
    Args:
        output_path: Path to output PDF file
        reconciled_df: Reconciled inventory DataFrame
        issues_df: Issues DataFrame
        summary: Summary statistics dictionary
        ordered_df: Optional ordered DataFrame for detailed view
        sold_df: Optional sold DataFrame for detailed view
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    # Title Page
    story.append(Paragraph("DawaiRx", title_style))
    story.append(Paragraph("Pharmacy Audit & Reconciliation Report", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(PageBreak())
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Medicines', f"{summary.get('total_medicines', 0):,}"],
        ['Total Ordered', f"{summary.get('total_ordered', 0):,.0f}"],
        ['Total Sold', f"{summary.get('total_sold', 0):,.0f}"],
        ['Total Remaining', f"{summary.get('total_remaining', 0):,.0f}"],
        ['Total Shortage', f"{summary.get('total_shortage', 0):,.0f}"],
        ['Total Leftover', f"{summary.get('total_leftover', 0):,.0f}"],
        ['Medicines with Shortage', f"{summary.get('medicines_with_shortage', 0):,}"],
        ['Medicines with Leftover', f"{summary.get('medicines_with_leftover', 0):,}"],
        ['Total Issues Found', f"{summary.get('total_issues', 0):,}"],
    ]
    
    if 'sold_percentage' in summary:
        summary_data.append(['Sold Percentage', f"{summary['sold_percentage']:.1f}%"])
    
    if 'issues_by_severity' in summary:
        sev = summary['issues_by_severity']
        summary_data.append(['High Severity Issues', f"{sev.get('high', 0):,}"])
        summary_data.append(['Medium Severity Issues', f"{sev.get('medium', 0):,}"])
        summary_data.append(['Low Severity Issues', f"{sev.get('low', 0):,}"])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    
    story.append(summary_table)
    story.append(PageBreak())
    
    # Issues Summary by Rule
    if len(issues_df) > 0:
        story.append(Paragraph("Audit Issues Summary", heading_style))
        
        # Group issues by rule_id
        issues_by_rule = issues_df.groupby('rule_id').agg({
            'rule_id': 'count',
            'severity': 'first'
        }).rename(columns={'rule_id': 'count'}).reset_index()
        issues_by_rule = issues_by_rule.sort_values('count', ascending=False)
        
        issues_summary_data = [['Rule ID', 'Severity', 'Count']]
        for _, row in issues_by_rule.iterrows():
            issues_summary_data.append([
                row['rule_id'],
                row['severity'],
                str(row['count'])
            ])
        
        issues_summary_table = Table(issues_summary_data, colWidths=[1.5*inch, 1.5*inch, 1*inch])
        issues_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(issues_summary_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Detailed Issues (first 50)
        story.append(Paragraph("Detailed Issues (Sample)", styles['Heading3']))
        
        issues_sample = issues_df.head(50)
        issues_data = [['Rule ID', 'Severity', 'Medicine', 'Details']]
        
        for _, issue in issues_sample.iterrows():
            issues_data.append([
                issue.get('rule_id', ''),
                issue.get('severity', ''),
                issue.get('medicine_key', 'N/A')[:30] if pd.notna(issue.get('medicine_key')) else 'N/A',
                issue.get('details', '')[:60] + '...' if len(str(issue.get('details', ''))) > 60 else str(issue.get('details', ''))
            ])
        
        issues_table = Table(issues_data, colWidths=[1*inch, 1*inch, 1.5*inch, 2.5*inch])
        issues_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        
        story.append(issues_table)
        
        if len(issues_df) > 50:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                f"<i>Showing first 50 of {len(issues_df)} total issues. See full CSV export for complete list.</i>",
                styles['Normal']
            ))
        
        story.append(PageBreak())
    
    # Shortages Section
    shortages = reconciled_df[reconciled_df["shortage_qty"] > 0].copy()
    if len(shortages) > 0:
        story.append(Paragraph("Shortages (Over-Sold Medicines)", heading_style))
        
        shortages_data = [['Medicine', 'NDC', 'Ordered', 'Sold', 'Shortage']]
        for _, row in shortages.head(30).iterrows():
            shortages_data.append([
                str(row.get('drug_name', 'N/A'))[:25],
                str(row.get('ndc', 'N/A'))[:15],
                f"{row.get('ordered_total', 0):,.0f}",
                f"{row.get('sold_total', 0):,.0f}",
                f"{row.get('shortage_qty', 0):,.0f}"
            ])
        
        shortages_table = Table(shortages_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
        shortages_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(shortages_table)
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Total shortages: {len(shortages)} medicines", styles['Normal']))
        story.append(PageBreak())
    
    # Remaining Inventory Section
    remaining = reconciled_df[reconciled_df["leftover_qty"] > 0].copy()
    if len(remaining) > 0:
        story.append(Paragraph("Remaining Inventory", heading_style))
        
        remaining_data = [['Medicine', 'NDC', 'Ordered', 'Sold', 'Remaining']]
        for _, row in remaining.head(30).iterrows():
            remaining_data.append([
                str(row.get('drug_name', 'N/A'))[:25],
                str(row.get('ndc', 'N/A'))[:15],
                f"{row.get('ordered_total', 0):,.0f}",
                f"{row.get('sold_total', 0):,.0f}",
                f"{row.get('leftover_qty', 0):,.0f}"
            ])
        
        remaining_table = Table(remaining_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
        remaining_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(remaining_table)
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Total medicines with remaining inventory: {len(remaining)}", styles['Normal']))
        story.append(PageBreak())
    
    # Reconciliation Details (Top 50 medicines)
    story.append(Paragraph("Reconciliation Details (Sample)", heading_style))
    
    sample_reconciled = reconciled_df.head(50)
    recon_data = [['Medicine', 'NDC', 'Ordered', 'Sold', 'Remaining', 'Status']]
    
    for _, row in sample_reconciled.iterrows():
        status = "Shortage" if row.get('shortage_qty', 0) > 0 else "OK" if row.get('leftover_qty', 0) == 0 else "Leftover"
        recon_data.append([
            str(row.get('drug_name', 'N/A'))[:20],
            str(row.get('ndc', 'N/A'))[:12],
            f"{row.get('ordered_total', 0):,.0f}",
            f"{row.get('sold_total', 0):,.0f}",
            f"{row.get('remaining_qty', 0):,.0f}",
            status
        ])
    
    recon_table = Table(recon_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    recon_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    
    story.append(recon_table)
    
    if len(reconciled_df) > 50:
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            f"<i>Showing first 50 of {len(reconciled_df)} total medicines. See full CSV export for complete list.</i>",
            styles['Normal']
        ))
    
    # Footer
    story.append(PageBreak())
    story.append(Paragraph("Report End", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        f"This report was generated by DawaiRx on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        styles['Italic']
    ))
    
    # Build PDF
    doc.build(story)
    logger.info(f"Created detailed PDF report: {output_path}")

