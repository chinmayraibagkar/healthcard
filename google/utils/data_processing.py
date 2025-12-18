"""
Data processing utilities
"""
import pandas as pd
from typing import Dict, Any, List


def flatten_results(results: Dict[int, Dict[str, Any]]) -> pd.DataFrame:
    """
    Flatten check results into a DataFrame.
    """
    data = []
    for check_num, result in results.items():
        data.append({
            "Check #": check_num,
            "Name": result.get("name", ""),
            "Status": result.get("status", ""),
            "Score": result.get("score", None),
            "Message": result.get("message", ""),
            "Threshold": result.get("threshold", "")
        })
    return pd.DataFrame(data)


def aggregate_issues(results: Dict[int, Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate all issues from failed checks.
    """
    all_issues = []
    
    for check_num, result in results.items():
        if result.get("status") in ["fail", "warning"]:
            details = result.get("details", pd.DataFrame())
            issues = result.get("issues", pd.DataFrame())
            
            for df in [details, issues]:
                if isinstance(df, pd.DataFrame) and not df.empty:
                    df_copy = df.copy()
                    df_copy["Check #"] = check_num
                    df_copy["Check Name"] = result.get("name", "")
                    all_issues.append(df_copy)
    
    if all_issues:
        return pd.concat(all_issues, ignore_index=True)
    return pd.DataFrame()


def calculate_overall_health_score(results: Dict[int, Dict[str, Any]]) -> float:
    """
    Calculate an overall health score based on all check results.
    """
    scores = []
    weights = {
        "pass": 1.0,
        "warning": 0.7,
        "fail": 0.0,
        "info": None,  # Don't count info checks
        "error": 0.0
    }
    
    for result in results.values():
        status = result.get("status", "info")
        score = result.get("score")
        
        if score is not None:
            scores.append(score)
        elif status in weights and weights[status] is not None:
            scores.append(weights[status] * 100)
    
    return sum(scores) / len(scores) if scores else 0


def format_currency(value: float, currency: str = "USD") -> str:
    """
    Format a value as currency.
    """
    if pd.isna(value):
        return "N/A"
    return f"{currency} {value:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a value as percentage.
    """
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}%"
