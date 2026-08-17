import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "ShipGuard — Technical Architecture & Project Portfolio")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)
            
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, page_text)
        self.drawString(54, 36, "Confidential — Prepared for Technical Evaluation & Interview")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * 72 - 54, 48)
        self.restoreState()


def build_pdf(filename="ShipGuard_Technical_Project_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#0F172A")    # Slate 900
    accent_blue = colors.HexColor("#2563EB")      # Blue 600
    text_dark = colors.HexColor("#1E293B")        # Slate 800
    text_muted = colors.HexColor("#64748B")       # Slate 500
    bg_light = colors.HexColor("#F8FAFC")         # Slate 50

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=accent_blue,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=accent_blue,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_dark,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#1E3A8A"),
    )

    story = []

    # Title & Metadata Header
    story.append(Paragraph("ShipGuard — Predictive Freight Intelligence Platform", title_style))
    story.append(Paragraph("Shipment Delay Risk Forecasting, Real-World Telemetry & GenAI Operations Engine", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_blue, spaceBefore=0, spaceAfter=10))

    # Meta banner table
    meta_data = [
        [
            Paragraph("<b>Project:</b> ShipGuard (Fresa Technologies)", body_style),
            Paragraph("<b>Architecture:</b> React 18 + FastAPI + Python ML + Oracle / SQLite", body_style)
        ],
        [
            Paragraph("<b>Author:</b> Mahan (mahanithi-dev)", body_style),
            Paragraph("<b>GitHub:</b> github.com/mahanithi-dev/fresa-shipguard", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[240, 264])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    exec_summary_text = (
        "In global freight forwarding, unexpected delays result in severe financial penalties (demurrage, detention) "
        "and degraded service reliability. <b>ShipGuard</b> is an enterprise-grade predictive intelligence system "
        "engineered to shift logistics operations from reactive fire-fighting to proactive risk prevention. "
        "The platform calculates transit delay probabilities before vessel departure, continuously ingests real-world "
        "telemetry (weather events, terminal dwell times, public holidays, currency shifts), and utilizes Large Language Models "
        "(Google Gemini & NVIDIA NIM) to generate automated root-cause explanations and operational action plans in real-time."
    )
    
    callout_data = [[Paragraph(exec_summary_text, callout_style)]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 8))

    # Section 2: Business Problems & Core Solutions
    story.append(Paragraph("2. Business Problems & Applied Solutions", h1_style))
    prob_data = [
        [
            Paragraph("<b>Logistics Operational Challenge</b>", ParagraphStyle('TH', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Business Impact</b>", ParagraphStyle('TH', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>ShipGuard Solution</b>", ParagraphStyle('TH', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white))
        ],
        [
            Paragraph("<b>Blind Spot Exceptions</b><br/>Delays only discovered after containers are stranded at transshipment hubs.", body_style),
            Paragraph("High demurrage/detention fees, SLA breach penalties.", body_style),
            Paragraph("<b>Predictive Risk Scoring:</b> Forecasts delay risk (Low/Med/High) 48-72h prior to occurrence.", body_style)
        ],
        [
            Paragraph("<b>Disconnected Telemetry</b><br/>Severe weather, port strikes, and local holidays ignored by static ERPs.", body_style),
            Paragraph("Unanticipated schedule disruptions and vessel rollover.", body_style),
            Paragraph("<b>Live External Sync:</b> Dynamic risk delta adjustments based on live API signals.", body_style)
        ],
        [
            Paragraph("<b>Communication Overheads</b><br/>Operations managers spend hours writing status emails & reports.", body_style),
            Paragraph("Slow turnaround time, lost operational focus.", body_style),
            Paragraph("<b>GenAI Incident Co-Pilot:</b> One-click delay notifications, mitigation plans & reports.", body_style)
        ],
        [
            Paragraph("<b>Data Leakage in Traditional ML</b><br/>Future milestone data contaminating training features.", body_style),
            Paragraph("Overly optimistic models that fail in live production.", body_style),
            Paragraph("<b>Point-in-Time Queries:</b> Strict historical boundaries based only on data before ETD.", body_style)
        ]
    ]
    prob_table = Table(prob_data, colWidths=[168, 150, 186])
    prob_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(prob_table)
    story.append(Spacer(1, 10))

    # Section 3: Architecture & Technology Stack
    story.append(Paragraph("3. Technical Architecture & Component Stack", h1_style))
    tech_data = [
        [
            Paragraph("<b>Layer</b>", ParagraphStyle('TH2', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Technology</b>", ParagraphStyle('TH2', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Architecture & Implementation Details</b>", ParagraphStyle('TH2', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white))
        ],
        [
            Paragraph("<b>Frontend</b>", body_style),
            Paragraph("React 18, Vite, Vanilla CSS", body_style),
            Paragraph("High-performance single-page app (SPA); operational dashboard with risk lane filters, modal telemetry, live metrics, and real-time AI assistant interface.", body_style)
        ],
        [
            Paragraph("<b>Backend API</b>", body_style),
            Paragraph("FastAPI, Python 3.11+, Pydantic", body_style),
            Paragraph("Asynchronous RESTful architecture with automated OpenAPI documentation, strict request/response data contracts, and dependency injection.", body_style)
        ],
        [
            Paragraph("<b>AI / ML Layer</b>", body_style),
            Paragraph("Scikit-Learn, NumPy, Custom Sigmoid Engine", body_style),
            Paragraph("Probabilistic feature extraction combining route baselines, carrier historical reliability, transit variances, and weather/port delta modifiers.", body_style)
        ],
        [
            Paragraph("<b>GenAI Services</b>", body_style),
            Paragraph("Google Gemini API & NVIDIA NIM", body_style),
            Paragraph("Multi-turn operations co-pilot, automated natural language incident reports, structured prompt engineering with dynamic context injection.", body_style)
        ],
        [
            Paragraph("<b>Database</b>", body_style),
            Paragraph("Oracle DB (Prod) / SQLite (Dev)", body_style),
            Paragraph("Dual-database architecture: Enterprise Oracle Autonomous DB schema (DDL, identity sequences, indexes) + zero-configuration SQLite for local dev/demos.", body_style)
        ],
        [
            Paragraph("<b>Security</b>", body_style),
            Paragraph("JWT Auth, bcrypt, Rate Limiter", body_style),
            Paragraph("Stateless Bearer token auth, salted password encryption, and multi-tier sliding-window rate limiters preventing API abuse and quota exhaustion.", body_style)
        ]
    ]
    tech_table = Table(tech_data, colWidths=[80, 140, 284])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # Section 4: Key Functional Modules
    story.append(Paragraph("4. Core Functional Modules", h1_style))
    
    story.append(Paragraph("A. Predictive Risk Scoring Engine", h2_style))
    story.append(Paragraph(
        "Scores each shipment continuously on a 0.0% to 99.9% probability scale, classifying shipments into actionable risk tiers: "
        "<b>LOW (<33%)</b> for standard milestone tracking; <b>MEDIUM (33%-65%)</b> for pre-emptive status alerts; and "
        "<b>HIGH (≥66%)</b> for immediate operational intervention and carrier escalation.", body_style
    ))

    story.append(Paragraph("B. External Real-World Telemetry Ingestion", h2_style))
    story.append(Paragraph(
        "A background telemetry worker periodically pulls external environmental factors to modify baseline risk scores:", body_style
    ))
    story.append(Paragraph("• <b>Port Weather:</b> Ingests wind speeds, storm warnings, and heavy precipitation (+4% to +12% risk delta).", bullet_style))
    story.append(Paragraph("• <b>Terminal Congestion:</b> Analyzes vessel queue lengths and average dwell times at transshipment ports (+15% risk delta).", bullet_style))
    story.append(Paragraph("• <b>Customs / Public Holidays:</b> Evaluates destination country holiday calendars within a ±2 day ETA window (+5% risk delta).", bullet_style))
    story.append(Paragraph("• <b>Foreign Exchange Volatility:</b> Monitors currency shifts (e.g. USD/INR) that trigger customs clearance delays (+2% risk delta).", bullet_style))

    story.append(Paragraph("C. Generative AI Logistics Co-Pilot", h2_style))
    story.append(Paragraph(
        "Integrates Google Gemini & NVIDIA NIM to translate complex statistical variables into clear operational insights. "
        "Operators can perform natural language Q&A, generate delay notification emails to consignees with one click, "
        "and obtain instant 2-step actionable mitigation plans. Includes an autonomous fallback rule engine for 100% uptime.", body_style
    ))

    story.append(Spacer(1, 10))

    # Section 5: Mathematical & ML Formulation
    story.append(Paragraph("5. Mathematical Formulation & Scoring Algorithm", h1_style))
    story.append(Paragraph(
        "<b>1. Point-in-Time Historical Evaluation (Zero Data Leakage):</b><br/>"
        "To ensure models only learn from historical reality, all calculations query exclusively records completed before the shipment's ETD:",
        body_style
    ))
    story.append(Paragraph(
        "<code>Route_Delay_As_Of(T) = AVG(delay_days) WHERE event_timestamp &lt; ETD</code><br/>"
        "<code>Carrier_Reliability_As_Of(T) = (On_Time_Shipments &lt; ETD / Total_Shipments &lt; ETD) * 100</code>",
        code_style
    ))

    story.append(Paragraph(
        "<b>2. Multi-Factor Risk Score Equation:</b><br/>"
        "The raw input vector <i>z</i> combines normalized carrier reliability, historical lane delay, seasonal surges, cargo class, and transit variance:",
        body_style
    ))
    story.append(Paragraph(
        "<code>z = (70 - Carrier_Reliability)/18 + (Route_Delay)/3.5 + W_season + W_cargo + W_mode + max(0, -Transit_Delta)/4 - 1.2</code>",
        code_style
    ))
    story.append(Paragraph(
        "The base score is mapped to a probability via the Sigmoid function and adjusted with external real-world signals:",
        body_style
    ))
    story.append(Paragraph(
        "<code>Base_Score = 1 / (1 + exp(-z))</code><br/>"
        "<code>Final_Risk_Score = min(0.99, max(0.01, Base_Score + Sum(Delta_External)))</code>",
        code_style
    ))

    story.append(Spacer(1, 10))

    # Section 6: Database Entity Architecture
    story.append(Paragraph("6. Database Architecture & Schema Design", h1_style))
    story.append(Paragraph(
        "The relational database is normalized in 3NF across 6 core domain entities:", body_style
    ))
    
    db_entities = [
        [
            Paragraph("<b>Entity Table</b>", ParagraphStyle('TH3', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Primary Key</b>", ParagraphStyle('TH3', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Key Attributes & Relationships</b>", ParagraphStyle('TH3', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white))
        ],
        [
            Paragraph("<b>CARRIERS</b>", body_style),
            Paragraph("<code>carrier_id</code>", code_style),
            Paragraph("<code>carrier_code, carrier_name, on_time_pct_hist</code>. Tracks long-term carrier reliability.", body_style)
        ],
        [
            Paragraph("<b>ROUTES</b>", body_style),
            Paragraph("<code>route_id</code>", code_style),
            Paragraph("<code>origin_port, dest_port, mode, avg_transit_days</code>. Trade lane baseline transit profiles.", body_style)
        ],
        [
            Paragraph("<b>SHIPMENTS</b>", body_style),
            Paragraph("<code>shipment_id</code>", code_style),
            Paragraph("<code>shipment_ref, carrier_id, route_id, etd, eta, actual_arrival, cargo_type, status</code>. Active freight worklist.", body_style)
        ],
        [
            Paragraph("<b>RISK_SCORES</b>", body_style),
            Paragraph("<code>shipment_id</code> (1:1)", code_style),
            Paragraph("<code>risk_score, risk_tier, top_factors (JSON), recommendation, scored_at</code>. Live scoring cache.", body_style)
        ],
        [
            Paragraph("<b>SHIPMENT_HISTORY</b>", body_style),
            Paragraph("<code>history_id</code>", code_style),
            Paragraph("<code>shipment_id, event_type, delay_days, event_ts</code>. Historical audit trail for time-series analytics.", body_style)
        ],
        [
            Paragraph("<b>EXTERNAL_TELEMETRY</b>", body_style),
            Paragraph("<code>id</code>", code_style),
            Paragraph("Port weather conditions, terminal wait hours, holiday calendars, and FX exchange rates.", body_style)
        ]
    ]
    db_table = Table(db_entities, colWidths=[120, 90, 294])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(db_table)

    # Build document with canvas numbering
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {filename}")

if __name__ == '__main__':
    build_pdf()
