import pandas as pd
from dataclasses import dataclass


@dataclass
class SummaryResult:
    success: bool
    summary_text: str = ""
    error_message: str = ""
    skipped: bool = False


SYSTEM_PROMPT = (
    "You are a Senior Audit Partner at EY (Ernst & Young) with 20 years of experience in financial "
    "statement auditing, forensic accounting, and enterprise risk management. Your role is to review "
    "flagged journal entry anomalies and produce a concise, professional audit risk assessment."
)

USER_PROMPT_TEMPLATE = """You have received the output of an automated anomaly detection scan on a client's journal entries.

ANOMALY DETECTION RESULTS:
Total flags raised: {total_flags}
Severity breakdown:
- Critical: {critical}
- High: {high}
- Medium: {medium}
- Low: {low}

Rule summary (flags per rule):
{rule_summary}

Top flagged transactions (up to 20):
{flagged_sample}

Based on this data, produce a structured audit risk assessment in exactly this format:

## Executive Summary
[3-4 sentences summarising the key audit concerns and the overall risk posture of the engagement.]

## Key Findings
[Bullet list of the top risks identified, specific to the anomalies detected above.]

## Risk Assessment
Overall Risk Level: [Critical / High / Medium / Low]
[One sentence justifying the overall risk level.]

## Recommended Actions
[Numbered list of concrete next steps for the audit team.]
"""


class Agent3Summary:
    """Agent 3: AI Audit Summary — calls Claude to generate a structured senior-auditor narrative."""

    def run(
        self,
        flagged_df: pd.DataFrame,
        severity_counts: dict,
        rule_summary: dict,
        api_key: str,
    ) -> SummaryResult:
        if not api_key or not api_key.strip():
            return SummaryResult(
                success=False,
                skipped=True,
                error_message="No Anthropic API key provided. Agent 3 skipped."
            )

        try:
            import anthropic
        except ImportError:
            return SummaryResult(
                success=False,
                error_message="anthropic package not installed."
            )

        total_flags = len(flagged_df)
        rule_lines = "\n".join(f"  - {rule}: {count}" for rule, count in rule_summary.items())
        sample_cols = ["transaction_id", "flag_type", "severity", "details"]
        available = [c for c in sample_cols if c in flagged_df.columns]
        flagged_sample = (
            flagged_df[available].head(20).to_string(index=False)
            if not flagged_df.empty
            else "No flags detected."
        )

        user_prompt = USER_PROMPT_TEMPLATE.format(
            total_flags=total_flags,
            critical=severity_counts.get("Critical", 0),
            high=severity_counts.get("High", 0),
            medium=severity_counts.get("Medium", 0),
            low=severity_counts.get("Low", 0),
            rule_summary=rule_lines or "  None",
            flagged_sample=flagged_sample,
        )

        try:
            client = anthropic.Anthropic(api_key=api_key.strip())
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            summary_text = message.content[0].text
            return SummaryResult(success=True, summary_text=summary_text)
        except Exception as e:
            return SummaryResult(success=False, error_message=f"Claude API error: {e}")
