"""Service for generating data insights using DSPy."""

import logging
from typing import Optional, List, Dict, Any
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.insight import Insight
from src.models.dataset import Dataset
from src.models.query import Query
from src.schemas.insight import InsightCreate
from src.dspy_modules import configure_dspy, generate_insights
from src.dspy_modules.insight_generator import InsightGenerator
from src.services.dataset_service import DatasetService, sanitize_for_postgres_json

logger = logging.getLogger(__name__)


class InsightService:
    """Service for automatic insight generation with DSPy."""

    def __init__(self):
        """Initialize insight service with DSPy configuration."""
        self.dataset_service = DatasetService()
        self.insight_generator: Optional[InsightGenerator] = None

        try:
            configure_dspy()
            self.insight_generator = InsightGenerator()
            logger.info("DSPy configured successfully for InsightService")
        except Exception as e:
            logger.error(f"Failed to configure DSPy: {e}")
            self.insight_generator = None

    async def generate_dataset_insights(
        self,
        db: Session,
        dataset_id: str,
        max_insights: int = 5
    ) -> List[Insight]:
        """Generate insights for a dataset."""
        try:
            dataset = db.execute(
                select(Dataset).where(Dataset.id == dataset_id)
            ).scalar_one_or_none()

            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")

            if dataset.status != "ready":
                logger.warning(f"Dataset {dataset_id} is not ready (status: {dataset.status})")
                return []

            df = await self.dataset_service.get_dataset_data(dataset)

            insights_data = generate_insights(
                df=df,
                query_context="",
                insight_generator=self.insight_generator,
                max_insights=max_insights
            )

            created_insights = []
            import uuid

            for insight_data in insights_data:
                viz_config = self._generate_visualization_config(
                    insight_data["insight_type"],
                    insight_data.get("supporting_data", [])
                )

                insight = Insight(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset_id,
                    query_id=None,
                    insight_type=insight_data["insight_type"],
                    title=insight_data["title"][:200],
                    description=insight_data["description"],
                    confidence_score=insight_data["confidence_score"],
                    supporting_data=sanitize_for_postgres_json(insight_data.get("supporting_data")),
                    visualization_config=sanitize_for_postgres_json(viz_config)
                )
                db.add(insight)
                created_insights.append(insight)

            db.commit()

            logger.info(f"Generated {len(created_insights)} insights for dataset {dataset_id}")
            return created_insights

        except Exception as e:
            logger.error(f"Failed to generate insights for dataset {dataset_id}: {e}", exc_info=True)
            return []

    async def generate_query_insights(
        self,
        db: Session,
        query_id: str,
        max_insights: int = 3
    ) -> List[Insight]:
        """Generate insights related to a specific query."""
        try:
            query = db.execute(
                select(Query).where(Query.id == query_id)
            ).scalar_one_or_none()

            if not query or query.status != "success":
                logger.warning(f"Query {query_id} not found or not successful")
                return []

            dataset = db.execute(
                select(Dataset).where(Dataset.id == query.dataset_id)
            ).scalar_one_or_none()

            if not dataset or dataset.status != "ready":
                return []

            df = await self.dataset_service.get_dataset_data(dataset)

            query_context = f"User asked: '{query.natural_language_query}'. Query returned {query.row_count} rows."

            insights_data = generate_insights(
                df=df,
                query_context=query_context,
                insight_generator=self.insight_generator,
                max_insights=max_insights
            )

            created_insights = []
            import uuid

            for insight_data in insights_data:
                viz_config = self._generate_visualization_config(
                    insight_data["insight_type"],
                    insight_data.get("supporting_data", [])
                )

                insight = Insight(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset.id,
                    query_id=query_id,
                    insight_type=insight_data["insight_type"],
                    title=insight_data["title"][:200],
                    description=insight_data["description"],
                    confidence_score=insight_data["confidence_score"],
                    supporting_data=sanitize_for_postgres_json(insight_data.get("supporting_data")),
                    visualization_config=sanitize_for_postgres_json(viz_config)
                )
                db.add(insight)
                created_insights.append(insight)

            db.commit()

            logger.info(f"Generated {len(created_insights)} insights for query {query_id}")
            return created_insights

        except Exception as e:
            logger.error(f"Failed to generate insights for query {query_id}: {e}", exc_info=True)
            return []

    def create_insight(
        self,
        db: Session,
        insight_data: InsightCreate
    ) -> Insight:
        """Create a manual insight."""
        import uuid

        insight = Insight(
            id=str(uuid.uuid4()),
            dataset_id=insight_data.dataset_id,
            query_id=insight_data.query_id,
            insight_type=insight_data.insight_type,
            title=insight_data.title,
            description=insight_data.description,
            confidence_score=insight_data.confidence_score,
            supporting_data=sanitize_for_postgres_json(insight_data.supporting_data),
            visualization_config=sanitize_for_postgres_json(insight_data.visualization_config)
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)

        return insight

    def get_dataset_insights(
        self,
        db: Session,
        dataset_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Insight]:
        """Get insights for a dataset."""
        insights = db.execute(
            select(Insight)
            .where(Insight.dataset_id == dataset_id)
            .order_by(Insight.confidence_score.desc(), Insight.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        return list(insights)

    def get_query_insights(
        self,
        db: Session,
        query_id: str
    ) -> List[Insight]:
        """Get insights for a specific query."""
        insights = db.execute(
            select(Insight)
            .where(Insight.query_id == query_id)
            .order_by(Insight.confidence_score.desc())
        ).scalars().all()

        return list(insights)

    def get_insight(
        self,
        db: Session,
        insight_id: str
    ) -> Optional[Insight]:
        """Get a specific insight by ID."""
        insight = db.execute(
            select(Insight).where(Insight.id == insight_id)
        ).scalar_one_or_none()

        return insight

    def delete_insight(
        self,
        db: Session,
        insight_id: str
    ) -> bool:
        """Delete an insight."""
        insight = db.execute(
            select(Insight).where(Insight.id == insight_id)
        ).scalar_one_or_none()

        if not insight:
            return False

        db.delete(insight)
        db.commit()
        return True

    @staticmethod
    def _generate_visualization_config(
        insight_type: str,
        supporting_data: list
    ) -> dict:
        """Generate visualization configuration based on insight type."""
        config = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                }
            }
        }

        if not supporting_data:
            return config

        if insight_type == "correlation":
            return InsightService._generate_correlation_viz(supporting_data)
        elif insight_type == "trend":
            return InsightService._generate_trend_viz(supporting_data)
        elif insight_type == "distribution":
            return InsightService._generate_distribution_viz(supporting_data)
        elif insight_type == "anomaly":
            return InsightService._generate_anomaly_viz(supporting_data)
        elif insight_type in ["overview", "summary", "statistical"]:
            return InsightService._generate_overview_viz(supporting_data)
        
        return config

    @staticmethod
    def _generate_correlation_viz(supporting_data: list) -> dict:
        """Generate scatter plot for correlation insights."""
        config = {
            "type": "scatter",
            "data": {
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                },
                "scales": {
                    "x": {"title": {"display": True, "text": ""}},
                    "y": {"title": {"display": True, "text": ""}}
                }
            }
        }
        
        if isinstance(supporting_data, list) and len(supporting_data) > 0:
            first_item = supporting_data[0]
            if isinstance(first_item, dict):
                col1 = first_item.get('col1', 'Variable 1')
                col2 = first_item.get('col2', 'Variable 2')
                
                config["data"]["datasets"] = [{
                    "label": f"{col1} vs {col2}",
                    "data": [],
                    "backgroundColor": "rgba(75, 192, 192, 0.6)"
                }]
                config["options"]["scales"]["x"]["title"]["text"] = col1
                config["options"]["scales"]["y"]["title"]["text"] = col2
        
        return config

    @staticmethod
    def _generate_trend_viz(supporting_data: list) -> dict:
        """Generate line chart for trend insights."""
        config = {
            "type": "line",
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": False}
                }
            }
        }
        
        if isinstance(supporting_data, list) and len(supporting_data) > 0:
            first_item = supporting_data[0]
            if isinstance(first_item, dict):
                column = first_item.get("column", "Trend")
                direction = first_item.get("direction", "")
                
                color = "rgb(75, 192, 192)" if direction == "increasing" else "rgb(255, 99, 132)"
                
                config["data"]["datasets"] = [{
                    "label": f"{column} ({direction})",
                    "data": [],
                    "borderColor": color,
                    "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.1)"),
                    "tension": 0.4,
                    "fill": True
                }]
        
        return config

    @staticmethod
    def _generate_distribution_viz(supporting_data: list) -> dict:
        """Generate histogram/bar chart for distribution insights."""
        config = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Frequency"}}
                }
            }
        }
        
        if isinstance(supporting_data, list) and len(supporting_data) > 0:
            first_item = supporting_data[0]
            if isinstance(first_item, dict):
                column = first_item.get("column", "Distribution")
                
                config["data"]["datasets"] = [{
                    "label": column,
                    "data": [],
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1
                }]
        
        return config

    @staticmethod
    def _generate_anomaly_viz(supporting_data: list) -> dict:
        """Generate scatter plot for anomaly detection."""
        config = {
            "type": "scatter",
            "data": {
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": True, "text": "Outlier Detection"}
                }
            }
        }
        
        if isinstance(supporting_data, list) and len(supporting_data) > 0:
            first_item = supporting_data[0]
            if isinstance(first_item, dict):
                config["data"]["datasets"].append({
                    "label": "Normal Values",
                    "data": [],
                    "backgroundColor": "rgba(75, 192, 192, 0.6)"
                })
                
                config["data"]["datasets"].append({
                    "label": "Outliers",
                    "data": [],
                    "backgroundColor": "rgba(255, 99, 132, 0.8)",
                    "pointRadius": 6
                })
        
        return config

    @staticmethod
    def _generate_overview_viz(supporting_data: list) -> dict:
        """Generate appropriate visualization for overview/summary insights."""
        if not isinstance(supporting_data, list) or len(supporting_data) == 0:
            return InsightService._get_default_config()
        
        first_item = supporting_data[0]
        
        if isinstance(first_item, dict):
            return InsightService._generate_dict_based_viz(supporting_data)
        elif isinstance(first_item, (int, float)):
            return InsightService._generate_numeric_list_viz(supporting_data)
        elif isinstance(first_item, str):
            return InsightService._generate_categorical_viz(supporting_data)
        
        return InsightService._get_default_config()

    @staticmethod
    def _generate_dict_based_viz(supporting_data: List[Dict[str, Any]]) -> dict:
        """Generate visualization from dictionary-based supporting data."""
        first_item = supporting_data[0]
        keys = list(first_item.keys())
        
        has_column = 'column' in first_item
        has_category = 'category' in first_item or 'name' in first_item
        has_value = 'value' in first_item or 'count' in first_item or 'frequency' in first_item
        has_mean = 'mean' in first_item
        has_multiple_metrics = sum(1 for k in keys if k in ['mean', 'median', 'std', 'min', 'max']) > 1
        
        if has_multiple_metrics and has_column:
            return InsightService._generate_multi_metric_viz(supporting_data)
        
        if (has_category or has_column) and has_value:
            return InsightService._generate_category_value_viz(supporting_data)
        
        if has_mean and has_column:
            return InsightService._generate_stats_summary_viz(supporting_data)
        
        return InsightService._generate_generic_dict_viz(supporting_data)

    @staticmethod
    def _generate_category_value_viz(supporting_data: List[Dict[str, Any]]) -> dict:
        """Generate bar chart for category-value pairs."""
        config = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": [{
                    "label": "Count",
                    "data": [],
                    "backgroundColor": [
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(153, 102, 255, 0.6)',
                        'rgba(255, 159, 64, 0.6)',
                        'rgba(199, 199, 199, 0.6)',
                        'rgba(83, 102, 255, 0.6)',
                    ],
                    "borderColor": [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)',
                        'rgba(199, 199, 199, 1)',
                        'rgba(83, 102, 255, 1)',
                    ],
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": False},
                    "title": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Count"}}
                }
            }
        }
        
        for item in supporting_data[:15]:
            label = (item.get('category') or item.get('name') or 
                    item.get('column') or item.get('label') or 
                    item.get('key') or str(item.get('id', '')))
            
            value = (item.get('count') or item.get('value') or 
                    item.get('frequency') or item.get('total') or 0)
            
            if label:
                config["data"]["labels"].append(str(label))
                config["data"]["datasets"][0]["data"].append(float(value) if value else 0)
        
        if supporting_data and 'count' in supporting_data[0]:
            config["data"]["datasets"][0]["label"] = "Count"
        elif supporting_data and 'frequency' in supporting_data[0]:
            config["data"]["datasets"][0]["label"] = "Frequency"
        elif supporting_data and 'value' in supporting_data[0]:
            config["data"]["datasets"][0]["label"] = "Value"
        
        return config

    @staticmethod
    def _generate_multi_metric_viz(supporting_data: List[Dict[str, Any]]) -> dict:
        """Generate grouped bar chart for multiple metrics per category."""
        config = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True}
                }
            }
        }
        
        config["data"]["labels"] = [item.get('column', f'Col {i}') 
                                     for i, item in enumerate(supporting_data[:10])]
        
        metrics = ['mean', 'median', 'std', 'min', 'max']
        colors = {
            'mean': 'rgba(54, 162, 235, 0.6)',
            'median': 'rgba(75, 192, 192, 0.6)',
            'std': 'rgba(255, 206, 86, 0.6)',
            'min': 'rgba(255, 99, 132, 0.6)',
            'max': 'rgba(153, 102, 255, 0.6)'
        }
        
        for metric in metrics:
            if metric in supporting_data[0]:
                dataset = {
                    "label": metric.capitalize(),
                    "data": [item.get(metric, 0) for item in supporting_data[:10]],
                    "backgroundColor": colors.get(metric, 'rgba(128, 128, 128, 0.6)'),
                    "borderWidth": 1
                }
                config["data"]["datasets"].append(dataset)
        
        return config

    @staticmethod
    def _generate_stats_summary_viz(supporting_data: List[Dict[str, Any]]) -> dict:
        """Generate visualization for statistical summary data."""
        config = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": [{
                    "label": "Mean",
                    "data": [],
                    "backgroundColor": 'rgba(54, 162, 235, 0.6)',
                    "borderColor": 'rgba(54, 162, 235, 1)',
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True}
                }
            }
        }
        
        for item in supporting_data[:10]:
            column = item.get('column', '')
            mean = item.get('mean', 0)
            
            if column:
                config["data"]["labels"].append(column)
                config["data"]["datasets"][0]["data"].append(float(mean) if mean else 0)
        
        return config

    @staticmethod
    def _generate_generic_dict_viz(supporting_data: List[Dict[str, Any]]) -> dict:
        """Fallback: Generate visualization from generic dictionary data."""
        config = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": [{
                    "label": "Values",
                    "data": [],
                    "backgroundColor": 'rgba(75, 192, 192, 0.6)',
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": False},
                    "title": {"display": False}
                }
            }
        }
        
        for item in supporting_data[:10]:
            if not isinstance(item, dict):
                continue
            
            label = None
            for key, value in item.items():
                if isinstance(value, str) or key in ['name', 'label', 'category', 'column']:
                    label = str(value)
                    break
            
            value = None
            for key, val in item.items():
                if isinstance(val, (int, float)):
                    value = val
                    break
            
            if label and value is not None:
                config["data"]["labels"].append(label)
                config["data"]["datasets"][0]["data"].append(value)
        
        return config

    @staticmethod
    def _generate_numeric_list_viz(supporting_data: List[float]) -> dict:
        """Generate visualization from list of numeric values."""
        config = {
            "type": "line",
            "data": {
                "labels": [str(i) for i in range(len(supporting_data[:50]))],
                "datasets": [{
                    "label": "Values",
                    "data": supporting_data[:50],
                    "borderColor": 'rgba(75, 192, 192, 1)',
                    "backgroundColor": 'rgba(75, 192, 192, 0.2)',
                    "tension": 0.1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                }
            }
        }
        return config

    @staticmethod
    def _generate_categorical_viz(supporting_data: List[str]) -> dict:
        """Generate visualization from list of categorical values."""
        counts = Counter(supporting_data)
        most_common = counts.most_common(15)
        
        config = {
            "type": "bar",
            "data": {
                "labels": [item[0] for item in most_common],
                "datasets": [{
                    "label": "Frequency",
                    "data": [item[1] for item in most_common],
                    "backgroundColor": 'rgba(54, 162, 235, 0.6)',
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": False},
                    "title": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Count"}}
                }
            }
        }
        return config

    @staticmethod
    def _get_default_config() -> dict:
        """Return default empty config."""
        return {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                }
            }
        }