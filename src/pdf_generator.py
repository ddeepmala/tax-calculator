import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

def add_footer(c, doc):
    c.saveState()
    c.setFont('Helvetica-Bold', 7)
    c.setFillColor(colors.HexColor('#1E293B')) # Dark Navy
    c.drawString(54, 45, "Built by Deepmala of Sweco India")
    c.drawString(54, 35, "For Learning Purpose and Personal Use Only")
    
    c.setFont('Helvetica', 7)
    c.drawRightString(doc.pagesize[0] - 54, 45, f"Page {doc.page}")
    
    # Disclaimer block
    c.setFont('Helvetica-Oblique', 6)
    c.setFillColor(colors.HexColor('#64748B')) # Soft Gray
    disclaimer_text_1 = "This tax planner is built by Deepmala of Sweco India for learning purposes and personal use only. The calculations are estimates based on configured"
    disclaimer_text_2 = "tax rules and are for informational/educational use. No warranty is provided regarding completeness, accuracy, or suitability. Users should verify"
    disclaimer_text_3 = "all calculations independently and consult a qualified Chartered Accountant or tax advisor for official tax planning and filing."
    
    c.drawCentredString(doc.pagesize[0] / 2.0, 25, disclaimer_text_1)
    c.drawCentredString(doc.pagesize[0] / 2.0, 17, disclaimer_text_2)
    c.drawCentredString(doc.pagesize[0] / 2.0, 9, disclaimer_text_3)
    
    c.restoreState()

def generate_tax_report_pdf(calc_result, output_path):
    """
    Generates a premium PDF report using ReportLab for A4 print.
    """
    # Setup document: A4 margins are 0.75 inch (54 points)
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=80 # High bottom margin to avoid overlapping our disclaimer footer
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    navy_primary = colors.HexColor('#1E3A8A')
    green_accent = colors.HexColor('#059669')
    gray_dark = colors.HexColor('#334155')
    gray_light = colors.HexColor('#F1F5F9')
    border_gray = colors.HexColor('#CBD5E1')
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=navy_primary,
        alignment=0, # Left-aligned
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569'),
        alignment=0,
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=navy_primary,
        spaceBefore=10,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=gray_dark
    )
    
    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white,
        alignment=1 # Centered
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=gray_dark
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )
    
    table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=table_cell_style,
        alignment=2 # Right
    )
    
    table_cell_right_bold = ParagraphStyle(
        'TableCellRightBold',
        parent=table_cell_bold,
        alignment=2 # Right
    )
    
    recom_banner_style = ParagraphStyle(
        'RecomBanner',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=green_accent,
        spaceBefore=10,
        spaceAfter=15
    )

    story = []
    
    # 1. Header
    story.append(Paragraph("India Salary Tax Planner FY 2026-27", title_style))
    story.append(Paragraph("Personalized Tax Computation and Regime Optimization Report (AY 2027-28)", subtitle_style))
    
    # 2. Personal & Summary Info
    p = calc_result['personal_details']
    s = calc_result['summary']
    
    summary_data = [
        [
            Paragraph("<b>Taxpayer Name:</b>", body_style), Paragraph(p['name'], body_style),
            Paragraph("<b>Gross Salary:</b>", body_style), Paragraph(f"Rs. {s['gross_salary']:,.2f}", body_bold)
        ],
        [
            Paragraph("<b>Age / Gender:</b>", body_style), Paragraph(f"{p['age']} Years / {p['gender']}", body_style),
            Paragraph("<b>Old Regime Tax:</b>", body_style), Paragraph(f"Rs. {s['old_tax_payable']:,.2f}", body_style)
        ],
        [
            Paragraph("<b>Residential Status:</b>", body_style), Paragraph(p['residential_status'], body_style),
            Paragraph("<b>New Regime Tax:</b>", body_style), Paragraph(f"Rs. {s['new_tax_payable']:,.2f}", body_style)
        ],
        [
            Paragraph("<b>Employment Sector:</b>", body_style), Paragraph(p['employment_sector'], body_style),
            Paragraph("<b>Recommended Regime:</b>", body_style), Paragraph(f"<b>{s['recommended_regime']}</b>", ParagraphStyle('RecText', parent=body_bold, textColor=green_accent))
        ]
    ]
    
    # Width of printable A4 page is ~487 points (595 - 108 margins)
    summary_table = Table(summary_data, colWidths=[120, 123, 120, 124])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), gray_light),
        ('BOX', (0,0), (-1,-1), 1, border_gray),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_gray),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # 3. Recommendation Banner
    recom_box_data = [[
        Paragraph(f"RECOMMENDATION: {s['recommended_regime']} is highly recommended for you.", table_cell_bold),
    ], [
        Paragraph(s['recommendation_details'], table_cell_style)
    ]]
    recom_table = Table(recom_box_data, colWidths=[487])
    recom_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')), # Very soft emerald green
        ('BOX', (0,0), (-1,-1), 1.5, green_accent),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(recom_table)
    story.append(Spacer(1, 15))
    
    # 4. Detailed side-by-side comparison
    story.append(Paragraph("Detailed Regime Comparison", section_title_style))
    
    old_br = calc_result['old_regime_breakdown']
    new_br = calc_result['new_regime_breakdown']
    
    comparison_data = [
        # Table Header
        [
            Paragraph("Tax Computation Head", table_header_style),
            Paragraph("Old Tax Regime (Rs.)", table_header_style),
            Paragraph("New Tax Regime (Rs.)", table_header_style)
        ],
        # Gross salary
        [
            Paragraph("<b>Gross Salary (A)</b>", table_cell_style),
            Paragraph(f"{old_br['gross_salary']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['gross_salary']:,.2f}", table_cell_right)
        ],
        # Exemptions
        [
            Paragraph("HRA Exemption u/s 10(13A)", table_cell_style),
            Paragraph(f"{old_br['hra_exemption']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        [
            Paragraph("Children Education Exemption u/s 10(14)", table_cell_style),
            Paragraph(f"{old_br['children_education_exemption']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        [
            Paragraph("Hostel Allowance Exemption u/s 10(14)", table_cell_style),
            Paragraph(f"{old_br['hostel_exemption']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        [
            Paragraph("LTA Exemption u/s 10(5)", table_cell_style),
            Paragraph(f"{old_br['lta_exemption']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        [
            Paragraph("Exempt Reimbursements (Fuel, Driver, Meal, etc.)", table_cell_style),
            Paragraph(f"{old_br['reimbursements_exemption']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        # Deductions
        [
            Paragraph("Standard Deduction u/s 16(ia)", table_cell_style),
            Paragraph(f"{old_br['standard_deduction']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['standard_deduction']:,.2f}", table_cell_right)
        ],
        [
            Paragraph("Professional Tax u/s 16(iii)", table_cell_style),
            Paragraph(f"{old_br['professional_tax']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        # Net salary
        [
            Paragraph("<b>Net Salary Income (B)</b>", table_cell_bold),
            Paragraph(f"<b>{old_br['net_salary']:,.2f}</b>", table_cell_right_bold),
            Paragraph(f"<b>{new_br['net_salary']:,.2f}</b>", table_cell_right_bold)
        ],
        # HP Income
        [
            Paragraph("Income from House Property (C)", table_cell_style),
            Paragraph(f"{old_br['house_property_income']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['house_property_income']:,.2f}", table_cell_right)
        ],
        # Other Sources
        [
            Paragraph("Income from Other Sources (D)", table_cell_style),
            Paragraph(f"{old_br['other_sources_income']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['other_sources_income']:,.2f}", table_cell_right)
        ],
        # Deductions (Chapter VI-A)
        [
            Paragraph("Section 80C Deductions (PF, PPF, ELSS, etc.)", table_cell_style),
            Paragraph(f"{old_br['deductions']['sec_80c']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        [
            Paragraph("Section 80CCD(1B) (Additional NPS)", table_cell_style),
            Paragraph(f"{old_br['deductions']['sec_80ccd_1b']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        [
            Paragraph("Section 80D (Health Insurance)", table_cell_style),
            Paragraph(f"{old_br['deductions']['sec_80d']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        [
            Paragraph("Section 80TTA / 80TTB (Interest Deduction)", table_cell_style),
            Paragraph(f"{old_br['deductions']['interest_deduction']:,.2f}", table_cell_right),
            Paragraph("Not Allowed", table_cell_right)
        ],
        [
            Paragraph("Employer NPS Contribution u/s 80CCD(2)", table_cell_style),
            Paragraph(f"{old_br['deductions']['sec_80ccd_2_employer']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['deductions']['sec_80ccd_2_employer']:,.2f}", table_cell_right)
        ],
        [
            Paragraph("Other Deductions (80E, 80G, 80U, etc.)", table_cell_style),
            Paragraph(f"{(old_br['deductions']['sec_80e'] + old_br['deductions']['sec_80g'] + old_br['deductions']['sec_80ee'] + old_br['deductions']['sec_80eea'] + old_br['deductions']['sec_80u'] + old_br['deductions']['sec_80dd']):,.2f}", table_cell_right),
            Paragraph(f"{new_br['deductions']['sec_80cch_agniveer']:,.2f}", table_cell_right)
        ],
        # Total Deductions
        [
            Paragraph("<b>Total Eligible Deductions (E)</b>", table_cell_bold),
            Paragraph(f"<b>{old_br['deductions']['total_deductions_eligible']:,.2f}</b>", table_cell_right_bold),
            Paragraph(f"<b>{new_br['deductions']['total_deductions_eligible']:,.2f}</b>", table_cell_right_bold)
        ],
        # Net Taxable Income
        [
            Paragraph("<b>Net Taxable Income (F = B+C+D-E)</b>", table_cell_bold),
            Paragraph(f"<b>{old_br['taxable_slab_income']:,.2f}</b>", table_cell_right_bold),
            Paragraph(f"<b>{new_br['taxable_slab_income']:,.2f}</b>", table_cell_right_bold)
        ],
        # Capital Gains
        [
            Paragraph("Capital Gains Income (STCG & LTCG) (G)", table_cell_style),
            Paragraph(f"{(old_br['stcg_equity'] + old_br['ltcg_equity']):,.2f}", table_cell_right),
            Paragraph(f"{(new_br['stcg_equity'] + new_br['ltcg_equity']):,.2f}", table_cell_right)
        ],
        # Slab Tax
        [
            Paragraph("Slab Tax (on progressive rates) (H)", table_cell_style),
            Paragraph(f"{old_br['slab_tax']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['slab_tax']:,.2f}", table_cell_right)
        ],
        # Capital Gains Tax
        [
            Paragraph("Capital Gains Tax (I)", table_cell_style),
            Paragraph(f"{(old_br['stcg_tax'] + old_br['ltcg_tax']):,.2f}", table_cell_right),
            Paragraph(f"{(new_br['stcg_tax'] + new_br['ltcg_tax']):,.2f}", table_cell_right)
        ],
        # Total Tax before rebate
        [
            Paragraph("Total Tax before Rebate (J = H+I)", table_cell_style),
            Paragraph(f"{old_br['tax_before_rebate']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['tax_before_rebate']:,.2f}", table_cell_right)
        ],
        # Section 87A rebate
        [
            Paragraph("Tax Rebate u/s 87A (K)", table_cell_style),
            Paragraph(f"- {old_br['sec_87a_rebate']:,.2f}", table_cell_right),
            Paragraph(f"- {new_br['sec_87a_rebate']:,.2f}", table_cell_right)
        ],
        # Section 87A marginal relief
        [
            Paragraph("Marginal Relief u/s 87A (L)", table_cell_style),
            Paragraph("0.00", table_cell_right),
            Paragraph(f"- {new_br['sec_87a_marginal_relief']:,.2f}", table_cell_right)
        ],
        # Surcharge
        [
            Paragraph("Surcharge (M)", table_cell_style),
            Paragraph(f"{old_br['surcharge']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['surcharge']:,.2f}", table_cell_right)
        ],
        # Cess
        [
            Paragraph("Health & Education Cess @ 4% (N)", table_cell_style),
            Paragraph(f"{old_br['cess']:,.2f}", table_cell_right),
            Paragraph(f"{new_br['cess']:,.2f}", table_cell_right)
        ],
        # Final tax
        [
            Paragraph("<b>Total Tax Payable (J - K - L + M + N)</b>", table_cell_bold),
            Paragraph(f"<b>{old_br['total_tax']:,.2f}</b>", table_cell_right_bold),
            Paragraph(f"<b>{new_br['total_tax']:,.2f}</b>", table_cell_right_bold)
        ],
    ]
    
    comp_table = Table(comparison_data, colWidths=[207, 140, 140])
    
    # Generate alternating backgrounds and border styles
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), navy_primary),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 1, border_gray),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_gray),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]
    
    # Alternating row colors
    for idx in range(1, len(comparison_data)):
        if idx in [1, 9, 18, 19, 28]: # Key summary rows
            t_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#F8FAFC')))
        elif idx % 2 == 0:
            t_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#FDFFFF')))
            
    comp_table.setStyle(TableStyle(t_style))
    story.append(KeepTogether([comp_table]))
    
    # Build document
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
