import dspy
from typing import List, Optional
import pandas as pd
import numpy as np
from scipy import stats


class InsightGenerationSignature(dspy.Signature):
    """Signature for generating insights from data analysis.

    This signature is optimized by DSPy to generate meaningful insights
    from statistical analysis and data patterns.
    """

    dataset_info: str = dspy.InputField(
        desc="Dataset overview including shape, columns, types, and basic statistics"
    )
    statistical_analysis: str = dspy.InputField(
        desc="Statistical analysis results including correlations, distributions, and anomalies"
    )
    query_context: str = dspy.InputField(
        desc="Optional context from a specific user query"
    )
    insight_type: str = dspy.OutputField(
        desc="Type of insight: trend, correlation, anomaly, distribution, statistical, or summary"
    )
    title: str = dspy.OutputField(
        desc="Clear, concise title for the insight (max 100 chars)"
    )
    description: str = dspy.OutputField(
        desc="Detailed description explaining the insight and its significance"
    )
    confidence_score: float = dspy.OutputField(
        desc="Confidence score from 0.0 to 1.0 indicating reliability of the insight"
    )
    recommendations: str = dspy.OutputField(
        desc="Actionable recommendations based on this insight"
    )


class InsightGenerator(dspy.Module):
    """DSPy module for generating data insights.

    This module uses Chain of Thought reasoning to analyze data
    and generate meaningful insights with high confidence.
    """

    def __init__(self):
        super().__init__()
        self.generate_insight = dspy.ChainOfThought(InsightGenerationSignature)

    def forward(
        self,
        dataset_info: str,
        statistical_analysis: str,
        query_context: str = ""
    ):
        """Generate an insight from data analysis.

        Args:
            dataset_info: Overview of the dataset
            statistical_analysis: Statistical findings
            query_context: Optional query context

        Returns:
            DSPy Prediction with insight details
        """
        prediction = self.generate_insight(
            dataset_info=dataset_info,
            statistical_analysis=statistical_analysis,
            query_context=query_context or "General dataset analysis"
        )
        return prediction


class DataAnalyzer:
    """Analyze data and extract statistical patterns for insight generation."""

    @staticmethod
    def analyze_dataframe(df: pd.DataFrame) -> dict:
        """Perform comprehensive statistical analysis on DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "overview": DataAnalyzer._get_overview(df),
            "correlations": DataAnalyzer._get_correlations(df),
            "distributions": DataAnalyzer._get_distributions(df),
            "anomalies": DataAnalyzer._detect_anomalies(df),
            "trends": DataAnalyzer._detect_trends(df),
        }
        return analysis

    @staticmethod
    def _get_overview(df: pd.DataFrame) -> dict:
        """Get dataset overview."""
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=["object"]).columns.tolist(),
            "missing_values": df.isnull().sum().to_dict(),
        }

    @staticmethod
    def _get_correlations(df: pd.DataFrame) -> List[dict]:
        """Find significant correlations."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return []

        corr_matrix = numeric_df.corr()
        correlations = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:
                    correlations.append({
                        "col1": corr_matrix.columns[i],
                        "col2": corr_matrix.columns[j],
                        "correlation": float(corr_value),
                        "strength": "strong" if abs(corr_value) > 0.7 else "moderate"
                    })

        return sorted(correlations, key=lambda x: abs(x["correlation"]), reverse=True)

    @staticmethod
    def _get_distributions(df: pd.DataFrame) -> List[dict]:
        """Analyze distributions of numeric columns."""
        numeric_df = df.select_dtypes(include=[np.number])
        distributions = []

        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            if len(data) < 3:
                continue

            _, p_value = stats.normaltest(data) if len(data) > 8 else (0, 1)

            distributions.append({
                "column": col,
                "mean": float(data.mean()),
                "median": float(data.median()),
                "std": float(data.std()),
                "skewness": float(data.skew()),
                "kurtosis": float(data.kurtosis()),
                "is_normal": bool(p_value > 0.05),
                "distribution_type": "normal" if p_value > 0.05 else "non-normal"
            })

        return distributions

    @staticmethod
    def _detect_anomalies(df: pd.DataFrame) -> List[dict]:
        """Detect anomalies using IQR method."""
        numeric_df = df.select_dtypes(include=[np.number])
        anomalies = []

        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            if len(data) < 4:
                continue

            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = data[(data < lower_bound) | (data > upper_bound)]
            if len(outliers) > 0:
                anomalies.append({
                    "column": col,
                    "outlier_count": len(outliers),
                    "outlier_percentage": float(len(outliers) / len(data) * 100),
                    "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)},
                    "outlier_values": outliers.head(5).tolist()
                })

        return anomalies

    @staticmethod
    def _detect_trends(df: pd.DataFrame) -> List[dict]:
        """Detect trends in numeric columns."""
        numeric_df = df.select_dtypes(include=[np.number])
        trends = []

        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            if len(data) < 3:
                continue

            x = np.arange(len(data))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)

            if abs(r_value) > 0.3 and p_value < 0.05: 
                trends.append({
                    "column": col,
                    "slope": float(slope),
                    "r_squared": float(r_value ** 2),
                    "direction": "increasing" if slope > 0 else "decreasing",
                    "strength": "strong" if abs(r_value) > 0.7 else "moderate"
                })

        return trends


def generate_insights(
    df: pd.DataFrame,
    query_context: str = "",
    insight_generator: Optional[InsightGenerator] = None,
    max_insights: int = 5
) -> List[dict]:
    """Generate multiple insights from a DataFrame.

    Args:
        df: Input DataFrame
        query_context: Optional context from user query
        insight_generator: Optional pre-configured InsightGenerator
        max_insights: Maximum number of insights to generate

    Returns:
        List of insight dictionaries
    """
    analyzer = DataAnalyzer()
    analysis = analyzer.analyze_dataframe(df)

    dataset_info = _format_dataset_info(df, analysis["overview"])
    statistical_analysis = _format_statistical_analysis(analysis)  # noqa: F841

    if insight_generator is None:
        insight_generator = InsightGenerator()

    insights = []

    insight_aspects = [
        ("correlation", analysis["correlations"][:2]),
        ("distribution", analysis["distributions"][:2]),
        ("anomaly", analysis["anomalies"][:2]),
        ("trend", analysis["trends"][:2]),
    ]

    for aspect_type, aspect_data in insight_aspects:
        if not aspect_data or len(insights) >= max_insights:
            continue

        aspect_analysis = _format_aspect_analysis(aspect_type, aspect_data)

        try:
            prediction = insight_generator.forward(
                dataset_info=dataset_info,
                statistical_analysis=aspect_analysis,
                query_context=query_context
            )

            insights.append({
                "insight_type": prediction.insight_type,
                "title": prediction.title,
                "description": prediction.description,
                "confidence_score": float(prediction.confidence_score),
                "recommendations": prediction.recommendations,
                "supporting_data": aspect_data if isinstance(aspect_data, list) else [aspect_data],
            })
        except Exception:
            continue

    return insights[:max_insights]


def _format_dataset_info(df: pd.DataFrame, overview: dict) -> str:
    """Format dataset information for insight generation."""
    info_parts = [
        f"Dataset: {overview['rows']} rows × {overview['columns']} columns",
        f"Numeric columns: {', '.join(overview['numeric_columns'])}",
        f"Categorical columns: {', '.join(overview['categorical_columns'])}",
    ]
    return "\n".join(info_parts)


def _format_statistical_analysis(analysis: dict) -> str:
    """Format statistical analysis for insight generation."""
    parts = []

    if analysis["correlations"]:
        parts.append("Strong Correlations Found:")
        for corr in analysis["correlations"][:3]:
            parts.append(
                f"- {corr['col1']} ↔ {corr['col2']}: {corr['correlation']:.2f} ({corr['strength']})"
            )

    if analysis["anomalies"]:
        parts.append("\nAnomalies Detected:")
        for anom in analysis["anomalies"][:3]:
            parts.append(
                f"- {anom['column']}: {anom['outlier_count']} outliers ({anom['outlier_percentage']:.1f}%)"
            )

    if analysis["trends"]:
        parts.append("\nTrends Identified:")
        for trend in analysis["trends"][:3]:
            parts.append(
                f"- {trend['column']}: {trend['direction']} trend (R²={trend['r_squared']:.2f})"
            )

    return "\n".join(parts) if parts else "No significant patterns detected."


def _format_aspect_analysis(aspect_type: str, aspect_data: list) -> str:
    """Format specific aspect analysis."""
    if not aspect_data:
        return f"No {aspect_type} patterns found."

    parts = [f"{aspect_type.capitalize()} Analysis:"]
    for item in aspect_data:
        parts.append(str(item))

    return "\n".join(parts)
