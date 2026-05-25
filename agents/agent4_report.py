import io
from datetime import date
from dataclasses import dataclass
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


@dataclass
class ReportResult:
    success: bool
    pdf_bytes: bytes = b""
    risk_score: int = 0
    risk_label: str = ""
    error_message: str = ""


SEVERITY_WEIGHTS = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}

EY_YELLOW = colors.HexColor("#FFE600")
EY_DARK = colors.HexColor("#2E2E38")
EY_GRAY = colors.HexColor("#747480")

SEVERITY_COLORS = {
    "Critical": colors.HexColor("#C0392B"),
    "High": colors.HexColor("#E67E22"),
    "Medium": colors.HexColor("#F1C40F"),
    "Low": colors.HexColor("#27AE60"),
}


def _risk_label(score: int) -> str:
    if score >= 40:
        return "Critical"
    if score >= 20:
        return "High"
    if score >= 8:
        return "Medium"
    return "Low"


class Agent4Report:
    """Agent 4: PDF Risk Report — compiles all agent outputs into a downloadable audit report."""

    def run(
        self,
        ingestion_result,
        anomaly_result,
        summary_result,
    ) -> ReportResult:
        try:
            severity_counts = anomaly_result.severity_counts
            risk_score = sum(
                SEVERITY_WEIGHTS.get(sev, 0) * cnt
                for sev, cnt in severity_counts.items()
            )
            label = _risk_label(risk_score)

            pdf_bytes = self._build_pdf(
                ingestion_result, anomaly_result, summary_result,
                risk_score, label
            )
            return ReportResult(
                success=True,
                pdf_bytes=pdf_bytes,
                risk_score=risk_score,
                risk_label=label,
            )
        except Exception as e:
            return ReportResult(success=False, error_message=f"PDF generation failed: {e}")

    def _build_pdf(self, ing, anom, summ, risk_score, risk_label):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "EYTitle",
            parent=styles["Title"],
            fontSize=22,
            textColor=EY_DARK,
            spaceAfter=4,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            "EYSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=EY_GRAY,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        h2_style = ParagraphStyle(
            "EYH2",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=EY_DARK,
            spaceBefore=14,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "EYBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=14,
        )
        footer_style = ParagraphStyle(
            "EYFooter",
            parent=styles["Normal"],
            fontSize=8,
            textColor=EY_GRAY,
            alignment=TA_CENTER,
        )

        story = []

        # Header bar (yellow strip effect via table)
        header_table = Table(
            [["EY Audit Risk Report"]],
            colWidths=[170 * mm],
        )
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), EY_YELLOW),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 18),
            ("TEXTCOLOR", (0, 0), (-1, -1), EY_DARK),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"Generated: {date.today().strftime('%d %B %Y')} &nbsp;|&nbsp; Client: [Company Placeholder]",
            subtitle_style
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=EY_GRAY))
        story.append(Spacer(1, 8))

        # Section 1: Data Overview
        story.append(Paragraph("Section 1 — Data Overview", h2_style))
        overview_data = [
            ["Metric", "Value"],
            ["Total Rows Processed", str(ing.row_count)],
            ["Total Columns Found", str(ing.column_count)],
            ["Rows with Null Values", str(ing.rows_with_nulls)],
            ["Validation Issues", str(len(ing.validation_issues))],
        ]
        t = Table(overview_data, colWidths=[85 * mm, 85 * mm])
        t.setStyle(self._base_table_style())
        story.append(t)

        if ing.validation_issues:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Validation Issues Detected:", h2_style))
            for issue in ing.validation_issues:
                story.append(Paragraph(f"• {issue}", body_style))

        # Section 2: Anomaly Detection
        story.append(Spacer(1, 8))
        story.append(Paragraph("Section 2 — Anomaly Detection Results", h2_style))

        sev_data = [["Severity", "Count"]]
        for sev in ["Critical", "High", "Medium", "Low"]:
            sev_data.append([sev, str(anom.severity_counts.get(sev, 0))])
        sev_table = Table(sev_data, colWidths=[85 * mm, 85 * mm])
        sev_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), EY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]
        for i, sev in enumerate(["Critical", "High", "Medium", "Low"], start=1):
            c = SEVERITY_COLORS.get(sev, colors.white)
            sev_cmds += [
                ("BACKGROUND", (0, i), (0, i), c),
                ("TEXTCOLOR", (0, i), (0, i), colors.white),
                ("FONTNAME", (0, i), (0, i), "Helvetica-Bold"),
            ]
        sev_table.setStyle(TableStyle(sev_cmds))
        story.append(sev_table)

        if not anom.flagged_df.empty:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Flagged Transactions (Top 25):", body_style))
            story.append(Spacer(1, 4))

            cols = ["transaction_id", "flag_type", "severity", "details"]
            available = [c for c in cols if c in anom.flagged_df.columns]
            sample = anom.flagged_df[available].head(25)

            flag_data = [available]
            for _, row in sample.iterrows():
                flag_data.append([str(row[c])[:60] for c in available])

            col_widths = [30 * mm, 45 * mm, 20 * mm, 75 * mm][:len(available)]
            ft = Table(flag_data, colWidths=col_widths, repeatRows=1)
            ft_cmds = self._base_table_cmds() + [
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("LEADING", (0, 0), (-1, -1), 10),
            ]
            ft.setStyle(TableStyle(ft_cmds))
            story.append(ft)

        # Section 3: AI Audit Summary
        story.append(Spacer(1, 8))
        story.append(Paragraph("Section 3 — AI Audit Summary", h2_style))
        if summ and summ.success and summ.summary_text:
            for line in summ.summary_text.split("\n"):
                stripped = line.strip()
                if not stripped:
                    story.append(Spacer(1, 4))
                elif stripped.startswith("## "):
                    story.append(Paragraph(stripped[3:], h2_style))
                else:
                    story.append(Paragraph(stripped, body_style))
        elif summ and summ.skipped:
            story.append(Paragraph("AI Audit Summary was skipped — no API key provided.", body_style))
        else:
            msg = summ.error_message if summ else "Agent 3 did not run."
            story.append(Paragraph(f"AI Summary unavailable: {msg}", body_style))

        # Section 4: Overall Risk Score
        story.append(Spacer(1, 8))
        story.append(Paragraph("Section 4 — Overall Risk Score", h2_style))
        score_color = SEVERITY_COLORS.get(risk_label, colors.gray)
        score_table = Table(
            [[f"Risk Score: {risk_score}", f"Risk Level: {risk_label}"]],
            colWidths=[85 * mm, 85 * mm],
        )
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), EY_DARK),
            ("BACKGROUND", (1, 0), (1, 0), score_color),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 14),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(score_table)

        score_formula = (
            f"Score formula: Critical×4 + High×3 + Medium×2 + Low×1 = "
            f"{anom.severity_counts.get('Critical',0)}×4 + "
            f"{anom.severity_counts.get('High',0)}×3 + "
            f"{anom.severity_counts.get('Medium',0)}×2 + "
            f"{anom.severity_counts.get('Low',0)}×1 = {risk_score}"
        )
        story.append(Spacer(1, 6))
        story.append(Paragraph(score_formula, body_style))

        # Footer
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=1, color=EY_GRAY))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "Generated by Multi-Agent Audit Assistant — Powered by Claude AI",
            footer_style
        ))

        doc.build(story)
        return buf.getvalue()

    def _base_table_cmds(self):
        return [
            ("BACKGROUND", (0, 0), (-1, 0), EY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]

    def _base_table_style(self):
        return TableStyle(self._base_table_cmds())
