import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnomalyResult:
    success: bool
    flagged_df: Optional[pd.DataFrame] = None
    total_flags: int = 0
    severity_counts: dict = field(default_factory=dict)
    rule_summary: dict = field(default_factory=dict)
    error_message: str = ""


ROUND_MULTIPLES = [1000, 5000, 10000]
OFF_HOURS_START = 22  # 10 PM
OFF_HOURS_END = 5     # 5 AM


class Agent2Anomaly:
    """Agent 2: Anomaly Detection — applies 6 audit rules to flag suspicious journal entries."""

    def run(self, df: pd.DataFrame) -> AnomalyResult:
        result = AnomalyResult(success=False)
        flags = []

        try:
            # Rule 1: Duplicate transaction IDs
            dup_mask = df.duplicated(subset=["transaction_id"], keep=False)
            for idx in df[dup_mask].index:
                tid = df.at[idx, "transaction_id"]
                flags.append({
                    "row_index": idx,
                    "transaction_id": tid,
                    "flag_type": "Duplicate Transaction ID",
                    "severity": "High",
                    "details": f"Transaction ID '{tid}' appears more than once."
                })

            # Rule 2: Round number transactions
            def is_round(val):
                try:
                    return any(float(val) % m == 0 for m in ROUND_MULTIPLES)
                except Exception:
                    return False

            for col in ("debit", "credit"):
                mask = df[col].apply(lambda v: is_round(v) if pd.notna(v) and v != 0 else False)
                for idx in df[mask].index:
                    flags.append({
                        "row_index": idx,
                        "transaction_id": df.at[idx, "transaction_id"],
                        "flag_type": "Round Number Transaction",
                        "severity": "Medium",
                        "details": f"{col.capitalize()} amount {df.at[idx, col]:,.2f} is an exact round number (fraud signal)."
                    })

            # Rule 3: Debit/credit imbalance per transaction group
            grouped = df.groupby("transaction_id").agg(
                total_debit=("debit", "sum"),
                total_credit=("credit", "sum")
            )
            imbalanced = grouped[~np.isclose(grouped["total_debit"], grouped["total_credit"], atol=0.01)]
            for tid in imbalanced.index:
                idx_list = df[df["transaction_id"] == tid].index.tolist()
                for idx in idx_list:
                    flags.append({
                        "row_index": idx,
                        "transaction_id": tid,
                        "flag_type": "Debit/Credit Imbalance",
                        "severity": "Critical",
                        "details": (
                            f"Total debits {imbalanced.at[tid, 'total_debit']:,.2f} ≠ "
                            f"total credits {imbalanced.at[tid, 'total_credit']:,.2f}."
                        )
                    })

            # Rule 4: Unusual amount (>3 std dev from mean)
            all_amounts = pd.concat([df["debit"], df["credit"]]).dropna()
            mean_amt = all_amounts.mean()
            std_amt = all_amounts.std()
            threshold = mean_amt + 3 * std_amt

            for col in ("debit", "credit"):
                mask = df[col] > threshold
                for idx in df[mask].index:
                    flags.append({
                        "row_index": idx,
                        "transaction_id": df.at[idx, "transaction_id"],
                        "flag_type": "Unusual Amount",
                        "severity": "High",
                        "details": (
                            f"{col.capitalize()} {df.at[idx, col]:,.2f} exceeds 3σ threshold "
                            f"({threshold:,.2f})."
                        )
                    })

            # Rule 5: Missing description
            missing_desc = df["description"].isna() | (df["description"].astype(str).str.strip() == "")
            for idx in df[missing_desc].index:
                flags.append({
                    "row_index": idx,
                    "transaction_id": df.at[idx, "transaction_id"],
                    "flag_type": "Missing Description",
                    "severity": "Low",
                    "details": "Transaction has no description — compliance risk."
                })

            # Rule 6: Off-hours entry (if date column has time info)
            if pd.api.types.is_datetime64_any_dtype(df["date"]):
                hours = df["date"].dt.hour
                off_hours_mask = (hours >= OFF_HOURS_START) | (hours < OFF_HOURS_END)
                for idx in df[off_hours_mask].index:
                    hour_val = df.at[idx, "date"].hour
                    flags.append({
                        "row_index": idx,
                        "transaction_id": df.at[idx, "transaction_id"],
                        "flag_type": "Off-Hours Entry",
                        "severity": "Medium",
                        "details": f"Entry logged at {hour_val:02d}:00 — outside business hours (10 PM – 5 AM)."
                    })

        except Exception as e:
            result.error_message = f"Anomaly detection failed: {e}"
            return result

        if flags:
            flagged_df = pd.DataFrame(flags)
        else:
            flagged_df = pd.DataFrame(columns=["row_index", "transaction_id", "flag_type", "severity", "details"])

        severity_order = ["Critical", "High", "Medium", "Low"]
        severity_counts = {s: int((flagged_df["severity"] == s).sum()) for s in severity_order}
        rule_summary = flagged_df["flag_type"].value_counts().to_dict() if not flagged_df.empty else {}

        result.success = True
        result.flagged_df = flagged_df
        result.total_flags = len(flagged_df)
        result.severity_counts = severity_counts
        result.rule_summary = rule_summary
        return result
