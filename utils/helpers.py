import streamlit as st
import pandas as pd

SEVERITY_COLORS = {
    "Critical": "#C0392B",
    "High": "#E67E22",
    "Medium": "#F1C40F",
    "Low": "#27AE60",
}

SEVERITY_BG = {
    "Critical": "#FDECEA",
    "High": "#FEF0E6",
    "Medium": "#FEFDE6",
    "Low": "#E9F7EF",
}


def severity_badge(severity: str) -> str:
    color = SEVERITY_COLORS.get(severity, "#999999")
    return (
        f'<span style="background-color:{color};color:white;'
        f'padding:2px 8px;border-radius:4px;font-size:12px;font-weight:bold;">'
        f'{severity}</span>'
    )


def styled_flagged_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p>No anomalies detected.</p>"

    rows = []
    for _, row in df.iterrows():
        sev = row.get("severity", "Low")
        bg = SEVERITY_BG.get(sev, "#FFFFFF")
        badge = severity_badge(sev)
        rows.append(
            f'<tr style="background-color:{bg};">'
            f'<td>{row.get("transaction_id","")}</td>'
            f'<td>{row.get("flag_type","")}</td>'
            f'<td>{badge}</td>'
            f'<td style="font-size:12px;">{row.get("details","")}</td>'
            f'</tr>'
        )

    header = (
        '<tr style="background-color:#2E2E38;color:white;font-weight:bold;">'
        '<th>Transaction ID</th><th>Flag Type</th>'
        '<th>Severity</th><th>Details</th></tr>'
    )
    table_html = (
        '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        f'{header}{"".join(rows)}</table>'
    )
    return table_html


def risk_score_badge(score: int, label: str) -> str:
    color = SEVERITY_COLORS.get(label, "#999999")
    return (
        f'<div style="display:inline-flex;gap:16px;align-items:center;">'
        f'<div style="background:#2E2E38;color:white;padding:12px 24px;'
        f'border-radius:8px;font-size:24px;font-weight:bold;">Score: {score}</div>'
        f'<div style="background:{color};color:white;padding:12px 24px;'
        f'border-radius:8px;font-size:24px;font-weight:bold;">{label} Risk</div>'
        f'</div>'
    )
