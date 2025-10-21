"""DSPy module for natural language to SQL conversion with improved column selection."""

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
        desc="Valid Pandas query or SQL-like expression. CRITICAL: Always include grouping columns in SELECT. Example: For 'count by category', use 'SELECT category, COUNT(*) as count GROUP BY category' not just 'SELECT COUNT(*)'"
    )
    explanation: str = dspy.OutputField(
        desc="Brief explanation of what the query does and how it answers the question"
    )
    visualization_type: str = dspy.OutputField(
        desc="Recommended visualization: bar_chart (for comparisons/aggregations), line_chart (for time series/trends), pie_chart (for distributions/percentages), number (for single values), or table (for complex/detailed data)"
    )


class NLToSQL(dspy.Module):
    """DSPy module for generating SQL queries from natural language.

    This module uses Chain of Thought reasoning to generate accurate SQL queries
    with proper column selection for meaningful results.
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
        enhanced_schema = f"{schema_info}\n\nIMPORTANT: When generating aggregation queries (COUNT, SUM, AVG, etc.), always include the grouping column(s) in the SELECT clause so results have meaningful labels."
        
        prediction = self.generate_query(
            schema_info=enhanced_schema,
            natural_language_query=natural_language_query
        )
        return prediction


class DataFrameQueryExecutor:
    """Execute queries on pandas DataFrames safely with improved grouping support."""

    @staticmethod
    def execute_query(df: pd.DataFrame, query: str) -> pd.DataFrame:
        """Execute a query on a DataFrame.

        Args:
            df: Input DataFrame
            query: Query string (pandas operations or SQL-like)

        Returns:
            Result DataFrame with proper column labels
        """
        try:
            if any(op in query.lower() for op in ['select', 'where', 'group by', 'order by']):
                result = DataFrameQueryExecutor._sql_to_pandas(df, query)
            else:
                result = eval(query, {"df": df, "pd": pd})

            if not isinstance(result, pd.DataFrame):
                if isinstance(result, pd.Series):
                    result = result.to_frame()
                else:
                    result = pd.DataFrame({"result": [result]})

            result = DataFrameQueryExecutor._ensure_meaningful_columns(result)
            
            return result
        except Exception as e:
            raise ValueError(f"Query execution failed: {str(e)}")

    @staticmethod
    def _ensure_meaningful_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure DataFrame has meaningful column names, not just indices."""
        if df.index.name and df.index.name not in df.columns:
            df = df.reset_index()
        elif not df.index.name and len(df.index.names) > 0 and df.index.names[0] is not None:
            df = df.reset_index()
        
        return df

    @staticmethod
    def _sql_to_pandas(df: pd.DataFrame, sql_query: str) -> pd.DataFrame:
        """Convert SQL-like queries to pandas operations with proper column handling."""
        query_lower = sql_query.lower().strip()

        if "count(*)" in query_lower and "group by" not in query_lower:
            return pd.DataFrame({"total_count": [len(df)]})

        if "group by" in query_lower:
            return DataFrameQueryExecutor._handle_group_by(df, sql_query, query_lower)

        if "order by" in query_lower:
            parts = query_lower.split("order by")
            col = parts[1].strip().split()[0]
            ascending = "desc" not in parts[1].lower()
            return df.sort_values(by=col, ascending=ascending)

        if "where" in query_lower:
            condition = query_lower.split("where")[1].strip()
            return df.query(condition)

        return df

    @staticmethod
    def _handle_group_by(df: pd.DataFrame, sql_query: str, query_lower: str) -> pd.DataFrame:
        """Handle GROUP BY queries with proper column selection."""
        try:
            group_by_part = query_lower.split("group by")[1].strip()
            group_cols = [col.strip() for col in group_by_part.split(",")[0].split()]
            group_col = group_cols[0]  # Primary grouping column
            
            if "order" in group_col:
                group_col = group_col.split("order")[0].strip()
            
            select_part = query_lower.split("from")[0].replace("select", "").strip()
            
            if "avg(" in select_part or "mean(" in select_part:
                if "avg(" in select_part:
                    agg_col = select_part.split("avg(")[1].split(")")[0].strip()
                else:
                    agg_col = select_part.split("mean(")[1].split(")")[0].strip()
                
                result = df.groupby(group_col)[agg_col].mean().reset_index()
                result.columns = [group_col, f"avg_{agg_col}"]
                
            elif "sum(" in select_part:
                agg_col = select_part.split("sum(")[1].split(")")[0].strip()
                result = df.groupby(group_col)[agg_col].sum().reset_index()
                result.columns = [group_col, f"sum_{agg_col}"]
                
            elif "count(" in select_part or "count(*)" in select_part:
                result = df.groupby(group_col).size().reset_index(name='count')
                
            elif "max(" in select_part:
                agg_col = select_part.split("max(")[1].split(")")[0].strip()
                result = df.groupby(group_col)[agg_col].max().reset_index()
                result.columns = [group_col, f"max_{agg_col}"]
                
            elif "min(" in select_part:
                agg_col = select_part.split("min(")[1].split(")")[0].strip()
                result = df.groupby(group_col)[agg_col].min().reset_index()
                result.columns = [group_col, f"min_{agg_col}"]
                
            else:
                result = df.groupby(group_col).size().reset_index(name='count')
            
            if "order by" in query_lower:
                order_part = query_lower.split("order by")[1].strip()
                if result.columns[1] in order_part or "count" in order_part or any(agg in order_part for agg in ["avg", "sum", "max", "min"]):
                    sort_col = result.columns[1]  # Sort by aggregate column
                else:
                    sort_col = result.columns[0]  # Sort by grouping column
                    
                ascending = "desc" not in order_part.lower()
                result = result.sort_values(by=sort_col, ascending=ascending)
            
            return result
            
        except Exception as e:
            try:
                for col in df.columns:
                    if col.lower() in query_lower:
                        return df.groupby(col).size().reset_index(name='count')
                return df.groupby(df.columns[0]).size().reset_index(name='count')
            except:
                raise ValueError(f"Could not parse GROUP BY query: {str(e)}")


def generate_sql_query(
    df: pd.DataFrame,
    natural_language_query: str,
    nl_to_sql_module: Optional[NLToSQL] = None
) -> dict:
    """Generate and execute SQL query from natural language with proper column labels.

    Args:
        df: Input DataFrame
        natural_language_query: User's question
        nl_to_sql_module: Optional pre-configured NLToSQL module

    Returns:
        Dictionary with query details and results
    """
    schema_info = _generate_schema_info(df)

    if nl_to_sql_module is None:
        nl_to_sql_module = NLToSQL()

    prediction = nl_to_sql_module.forward(
        schema_info=schema_info,
        natural_language_query=natural_language_query
    )

    # Execute 
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
    """Generate schema information from DataFrame with examples of grouping queries.

    Args:
        df: Input DataFrame

    Returns:
        Formatted schema string with query examples
    """
    schema_parts = []
    schema_parts.append(f"Dataset has {len(df)} rows and {len(df.columns)} columns.\n")
    schema_parts.append("Column Information:")

    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].count()
        null_pct = (len(df) - non_null) / len(df) * 100

        sample_values = df[col].dropna().head(3).tolist()

        if pd.api.types.is_numeric_dtype(df[col]):
            stats = f"min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}"
        else:
            unique_count = df[col].nunique()
            stats = f"unique_values={unique_count}"
            if unique_count < 50:
                top_values = df[col].value_counts().head(3).to_dict()
                stats += f", top_categories={top_values}"

        schema_parts.append(
            f"- {col}: type={dtype}, non_null={non_null} ({100-null_pct:.1f}%), "
            f"{stats}, samples={sample_values}"
        )
    
    schema_parts.append("\n⚠️ IMPORTANT QUERY FORMATTING:")
    schema_parts.append("- For aggregations, ALWAYS include the grouping column in SELECT")
    schema_parts.append("- Example: 'SELECT category, COUNT(*) as count GROUP BY category' ✅")
    schema_parts.append("- NOT: 'SELECT COUNT(*) GROUP BY category' ❌")
    schema_parts.append("- This ensures results have meaningful labels, not just values")

    return "\n".join(schema_parts)