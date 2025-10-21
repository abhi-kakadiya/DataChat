"""DSPy module for natural language to SQL conversion with prompt engineering."""

import dspy
from typing import Optional
import pandas as pd


class NLToSQLSignature(dspy.Signature):
    """Signature for converting natural language queries to SQL.

    This signature defines the input-output structure for prompt engineering.
    DSPy will optimize the prompts to improve SQL generation accuracy.
    """

    schema_info: str = dspy.InputField(
        desc="Database schema information including table name, column names, types, and sample values"
    )
    natural_language_query: str = dspy.InputField(
        desc="User's question in natural language about the data"
    )
    query_type: str = dspy.OutputField(
        desc="Type of query: aggregation, filtering, sorting, grouping, statistical, or visualization"
    )
    sql_query: str = dspy.OutputField(
        desc="Valid Pandas query or SQL-like expression to answer the question. Use pandas DataFrame methods."
    )
    explanation: str = dspy.OutputField(
        desc="Brief explanation of what the query does and how it answers the question"
    )
    visualization_type: str = dspy.OutputField(
        desc="Recommended visualization: bar_chart (for comparisons/aggregations), line_chart (for time series/trends), pie_chart (for distributions/percentages), number (for single values), or table (for complex/detailed data)"
    )


class NLToSQL(dspy.Module):
    """DSPy module for generating SQL queries from natural language.

    This module uses Chain of Thought reasoning to generate accurate SQL queries.
    It can be optimized using DSPy optimizers like BootstrapFewShot or MIPRO.
    """

    def __init__(self):
        super().__init__()
        self.generate_query = dspy.ChainOfThought(NLToSQLSignature)

    def forward(self, schema_info: str, natural_language_query: str):
        """Generate SQL query from natural language.

        Args:
            schema_info: Database schema with column information
            natural_language_query: User's question

        Returns:
            DSPy Prediction with query_type, sql_query, and explanation
        """
        prediction = self.generate_query(
            schema_info=schema_info,
            natural_language_query=natural_language_query
        )
        return prediction


class DataFrameQueryExecutor:
    """Execute queries on pandas DataFrames safely."""

    @staticmethod
    def execute_query(df: pd.DataFrame, query: str) -> pd.DataFrame:
        """Execute a query on a DataFrame.

        Args:
            df: Input DataFrame
            query: Query string (pandas operations or SQL-like)

        Returns:
            Result DataFrame
        """
        try:
            # Try pandas query method first
            if any(op in query.lower() for op in ['select', 'where', 'group by', 'order by']):
                # Convert SQL-like to pandas
                result = DataFrameQueryExecutor._sql_to_pandas(df, query)
            else:
                # Direct pandas operation
                result = eval(query, {"df": df, "pd": pd})

            if not isinstance(result, pd.DataFrame):
                if isinstance(result, pd.Series):
                    result = result.to_frame()
                else:
                    # Scalar result
                    result = pd.DataFrame({"result": [result]})

            return result
        except Exception as e:
            raise ValueError(f"Query execution failed: {str(e)}")

    @staticmethod
    def _sql_to_pandas(df: pd.DataFrame, sql_query: str) -> pd.DataFrame:
        """Convert simple SQL-like queries to pandas operations.

        This is a simplified converter for common SQL patterns.
        """
        query_lower = sql_query.lower().strip()

        # Handle SELECT COUNT(*)
        if "count(*)" in query_lower:
            return pd.DataFrame({"count": [len(df)]})

        # Handle GROUP BY with aggregation
        if "group by" in query_lower:
            # Simple pattern: SELECT col, AGG(col2) FROM table GROUP BY col
            parts = query_lower.split("group by")
            group_col = parts[1].strip().split()[0]

            if "avg(" in parts[0]:
                agg_col = parts[0].split("avg(")[1].split(")")[0]
                return df.groupby(group_col)[agg_col].mean().reset_index()
            elif "sum(" in parts[0]:
                agg_col = parts[0].split("sum(")[1].split(")")[0]
                return df.groupby(group_col)[agg_col].sum().reset_index()
            elif "count(" in parts[0]:
                return df.groupby(group_col).size().reset_index(name='count')

        # Handle ORDER BY
        if "order by" in query_lower:
            parts = query_lower.split("order by")
            col = parts[1].strip().split()[0]
            ascending = "desc" not in parts[1].lower()
            return df.sort_values(by=col, ascending=ascending)

        # Handle WHERE
        if "where" in query_lower:
            condition = query_lower.split("where")[1].strip()
            return df.query(condition)

        # Default: return original
        return df


def generate_sql_query(
    df: pd.DataFrame,
    natural_language_query: str,
    nl_to_sql_module: Optional[NLToSQL] = None
) -> dict:
    """Generate and execute SQL query from natural language.

    Args:
        df: Input DataFrame
        natural_language_query: User's question
        nl_to_sql_module: Optional pre-configured NLToSQL module

    Returns:
        Dictionary with query details and results
    """
    # Generate schema information
    schema_info = _generate_schema_info(df)

    # Create or use provided module
    if nl_to_sql_module is None:
        nl_to_sql_module = NLToSQL()

    # Generate SQL query
    prediction = nl_to_sql_module.forward(
        schema_info=schema_info,
        natural_language_query=natural_language_query
    )

    # Execute query
    try:
        executor = DataFrameQueryExecutor()
        result_df = executor.execute_query(df, prediction.sql_query)

        return {
            "query_type": prediction.query_type,
            "sql_query": prediction.sql_query,
            "explanation": prediction.explanation,
            "visualization_type": prediction.visualization_type,
            "result": result_df,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "query_type": prediction.query_type,
            "sql_query": prediction.sql_query,
            "explanation": prediction.explanation,
            "visualization_type": getattr(prediction, "visualization_type", "table"),
            "result": None,
            "success": False,
            "error": str(e)
        }


def _generate_schema_info(df: pd.DataFrame) -> str:
    """Generate schema information from DataFrame.

    Args:
        df: Input DataFrame

    Returns:
        Formatted schema string
    """
    schema_parts = []
    schema_parts.append(f"Dataset has {len(df)} rows and {len(df.columns)} columns.\n")
    schema_parts.append("Column Information:")

    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].count()
        null_pct = (len(df) - non_null) / len(df) * 100

        # Get sample values
        sample_values = df[col].dropna().head(3).tolist()

        # Statistics for numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            stats = f"min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}"
        else:
            unique_count = df[col].nunique()
            stats = f"unique_values={unique_count}"

        schema_parts.append(
            f"- {col}: type={dtype}, non_null={non_null} ({100-null_pct:.1f}%), "
            f"{stats}, samples={sample_values}"
        )

    return "\n".join(schema_parts)
