import pandas as pd
import io
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IngestionResult:
    success: bool
    df: Optional[pd.DataFrame] = None
    row_count: int = 0
    column_count: int = 0
    columns_found: list = field(default_factory=list)
    missing_columns: list = field(default_factory=list)
    validation_issues: list = field(default_factory=list)
    rows_with_nulls: int = 0
    error_message: str = ""


REQUIRED_COLUMNS = [
    "date", "transaction_id", "account_code", "account_name",
    "debit", "credit", "description", "auditor_id"
]


class Agent1Ingestion:
    """Agent 1: Data Ingestion & Validation — parses and validates journal entry CSV uploads."""

    def run(self, file_bytes: bytes) -> IngestionResult:
        result = IngestionResult(success=False)

        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            result.error_message = f"Failed to parse CSV: {e}"
            return result

        result.columns_found = list(df.columns)
        result.missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]

        if result.missing_columns:
            result.error_message = (
                f"Missing required columns: {', '.join(result.missing_columns)}. "
                f"Found: {', '.join(result.columns_found)}"
            )
            return result

        issues = []

        # Parse dates
        try:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            bad_dates = df["date"].isna().sum()
            if bad_dates:
                issues.append(f"{bad_dates} rows have unparseable dates.")
        except Exception as e:
            issues.append(f"Date parsing error: {e}")

        # Convert numeric columns
        for col in ("debit", "credit"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
            nulls = df[col].isna().sum()
            if nulls:
                issues.append(f"{nulls} rows have non-numeric values in '{col}'.")

        # Count rows with any null in required columns
        result.rows_with_nulls = int(df[REQUIRED_COLUMNS].isnull().any(axis=1).sum())
        if result.rows_with_nulls:
            issues.append(f"{result.rows_with_nulls} rows contain at least one missing value.")

        result.df = df
        result.row_count = len(df)
        result.column_count = len(df.columns)
        result.validation_issues = issues
        result.success = True
        return result
