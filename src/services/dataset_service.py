import io
import logging
import math
from typing import Any, Dict

import pandas as pd
from fastapi import UploadFile

from src.core.storage import storage_manager
from src.models.dataset import Dataset
from src.schemas.dataset import DatasetCreate

logger = logging.getLogger(__name__)


def sanitize_for_postgres_json(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: sanitize_for_postgres_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_postgres_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    return data


class DatasetService:
    def __init__(self):
        self.storage = storage_manager

    async def upload_dataset(
        self, file: UploadFile, dataset_data: DatasetCreate, owner_id: str
    ) -> Dataset:
        """Upload and process a dataset."""
        try:
            content = await file.read()
            file_size = len(content)

            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                raise ValueError(
                    f"File size {file_size} exceeds maximum allowed size {max_size}"
                )

            import uuid

            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{file.filename}"

            content_type = file.content_type
            if file.filename.endswith(".xlsx"):
                content_type = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif file.filename.endswith(".csv"):
                content_type = "text/csv"

            file_obj = io.BytesIO(content)
            file_path = await self.storage.upload_file(
                file_obj,
                filename,
                content_type=content_type,
                metadata={
                    "original_filename": file.filename,
                    "owner_id": owner_id,
                    "dataset_name": dataset_data.name,
                },
            )

            data_info = await self._process_file(content, file.filename)

            dataset = Dataset(
                name=dataset_data.name,
                description=dataset_data.description,
                filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                content_type=content_type,
                row_count=data_info.get("row_count"),
                column_count=data_info.get("column_count"),
                column_info=data_info.get("column_info"),
                status="ready",
                owner_id=owner_id,
            )

            return dataset

        except Exception as e:
            logger.error(f"Error uploading dataset: {str(e)}")
            raise

    async def get_dataset_preview(
        self, dataset: Dataset, limit: int = 10
    ) -> Dict[str, Any]:
        """Get dataset preview data."""
        try:
            file_content = await self.storage.download_file(
                dataset.file_path.split("/", 1)[1]
            )

            df = self._read_dataframe(file_content, dataset.filename)

            preview_data = df.head(limit).to_dict("records")

            return {
                "id": str(dataset.id),
                "name": dataset.name,
                "row_count": len(df),
                "column_count": len(df.columns),
                "column_info": self._get_column_info(df),
                "preview_data": preview_data,
                "status": dataset.status,
            }

        except Exception as e:
            logger.error(f"Error getting dataset preview: {str(e)}")
            raise

    async def get_dataset_data(self, dataset: Dataset) -> pd.DataFrame:
        """Get full dataset as DataFrame."""
        try:
            file_content = await self.storage.download_file(
                dataset.file_path.split("/", 1)[1]
            )

            df = self._read_dataframe(file_content, dataset.filename)

            return df

        except Exception as e:
            logger.error(f"Error getting dataset data: {str(e)}")
            raise

    def _read_dataframe(self, content: bytes, filename: str) -> pd.DataFrame:
        """Read DataFrame from bytes content based on file type."""
        try:
            if filename.endswith(".xlsx"):
                df = pd.read_excel(io.BytesIO(content))

                unnamed_cols = [
                    col for col in df.columns if str(col).startswith("Unnamed:")
                ]

                if len(unnamed_cols) > len(df.columns) / 2:
                    for skip_rows in range(5):
                        df_test = pd.read_excel(io.BytesIO(content), header=skip_rows)
                        unnamed_test = [
                            col
                            for col in df_test.columns
                            if str(col).startswith("Unnamed:")
                        ]
                        if len(unnamed_test) < len(df_test.columns) / 2:
                            df = df_test
                            break

                df = df.dropna(axis=1, how="all")

                df = df.dropna(axis=0, how="all")

                return df

            elif filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
                df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
                return df
            else:
                raise ValueError(f"Unsupported file type: {filename}")
        except Exception as e:
            logger.error(f"Error reading dataframe: {str(e)}")
            raise

    async def _process_file(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process file content and extract metadata."""
        try:
            df = self._read_dataframe(content, filename)

            column_info = self._get_column_info(df)

            return {
                "row_count": len(df),
                "column_count": len(df.columns),
                "column_info": column_info,
            }

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def _get_column_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get column information from DataFrame."""
        column_info = {}

        for col in df.columns:
            col_data = df[col]
            column_info[col] = {
                "type": str(col_data.dtype),
                "null_count": int(col_data.isnull().sum()),
                "null_percentage": float(
                    (col_data.isnull().sum() / len(col_data)) * 100
                ),
                "unique_count": int(col_data.nunique()),
                "sample_values": col_data.dropna().head(5).tolist(),
            }

            if pd.api.types.is_numeric_dtype(col_data):
                column_info[col].update(
                    {
                        "min": float(col_data.min()) if not col_data.empty else None,
                        "max": float(col_data.max()) if not col_data.empty else None,
                        "mean": float(col_data.mean()) if not col_data.empty else None,
                        "std": float(col_data.std()) if not col_data.empty else None,
                    }
                )

        # column_info = sanitize_for_postgres_json(column_info)

        return column_info

    def split_dataset(
        self, df: pd.DataFrame, train_size: int = 100, dev_size: int = 50
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Split dataset into train and dev sets."""
        try:
            total_size = len(df)
            if train_size + dev_size > total_size:
                ratio = total_size / (train_size + dev_size)
                train_size = int(train_size * ratio)
                dev_size = int(dev_size * ratio)

            train_df = df.head(train_size)
            dev_df = df.iloc[train_size : train_size + dev_size]

            return train_df, dev_df

        except Exception as e:
            logger.error(f"Error splitting dataset: {str(e)}")
            raise
