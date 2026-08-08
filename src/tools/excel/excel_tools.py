import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ExcelTool:
    """Reads, writes, analyzes, and visualizes spreadsheet data."""

    def read_rows(self, path: str, limit: int = 100) -> List[Dict[str, Any]]:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(path)

        if file_path.suffix.lower() == ".csv":
            with file_path.open(newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))[:limit]

        if not PANDAS_AVAILABLE:
            raise RuntimeError("Install pandas and openpyxl to read Excel files")

        frame = pd.read_excel(file_path)
        return frame.head(limit).to_dict(orient="records")

    def write_rows(self, path: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.suffix.lower() == ".csv":
            fieldnames = sorted({key for row in rows for key in row.keys()})
            with file_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return {"status": "success", "path": str(file_path), "rows": len(rows)}

        if not PANDAS_AVAILABLE:
            raise RuntimeError("Install pandas and openpyxl to write Excel files")

        pd.DataFrame(rows).to_excel(file_path, index=False)
        return {"status": "success", "path": str(file_path), "rows": len(rows)}

    def summarize_rows(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not rows:
            return {"rows": 0, "columns": []}
        columns = sorted({key for row in rows for key in row.keys()})
        return {"rows": len(rows), "columns": columns}

    def analyze(self, rows: List[Dict[str, Any]], analysis_type: str = "summary") -> Dict[str, Any]:
        if not rows:
            return {"error": "No data to analyze"}

        if not PANDAS_AVAILABLE:
            return self._basic_analyze(rows, analysis_type)

        df = pd.DataFrame(rows)
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if analysis_type == "summary":
            return {
                "rows": len(df),
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "numeric_summary": df[numeric_cols].describe().to_dict() if numeric_cols else {},
                "missing_values": df.isnull().sum().to_dict(),
            }
        elif analysis_type == "correlation" and len(numeric_cols) > 1:
            return {"correlation_matrix": df[numeric_cols].corr().to_dict()}
        elif analysis_type == "unique_counts":
            return {"unique_counts": {col: df[col].nunique() for col in df.columns}}
        elif analysis_type == "value_counts":
            categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
            return {col: df[col].value_counts().head(10).to_dict() for col in categorical_cols}
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}

    def _basic_analyze(self, rows: List[Dict[str, Any]], analysis_type: str) -> Dict[str, Any]:
        columns = sorted({key for row in rows for key in row.keys()})
        if analysis_type == "summary":
            return {"rows": len(rows), "columns": columns}
        return {"error": "Pandas required for advanced analysis"}

    def pivot_table(
        self,
        rows: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not PANDAS_AVAILABLE:
            return {"error": "Pandas required for pivot tables"}

        if not rows:
            return {"error": "No data for pivot table"}

        df = pd.DataFrame(rows)
        index = config.get("index")
        columns = config.get("columns")
        values = config.get("values")
        aggfunc = config.get("aggfunc", "sum")

        if not index or not values:
            return {"error": "Pivot config requires 'index' and 'values'"}

        try:
            pivot = pd.pivot_table(
                df,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc,
                fill_value=0,
            )
            return {
                "pivot_table": pivot.to_dict(),
                "index": index,
                "columns": columns,
                "values": values,
                "aggfunc": aggfunc,
            }
        except Exception as exc:
            return {"error": str(exc)}

    def create_chart(
        self,
        rows: List[Dict[str, Any]],
        config: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not PANDAS_AVAILABLE:
            return {"error": "Pandas required for charts"}

        if not rows:
            return {"error": "No data for chart"}

        df = pd.DataFrame(rows)
        chart_type = config.get("type", "bar")
        x_col = config.get("x")
        y_col = config.get("y")
        group_by = config.get("group_by")

        if not x_col or not y_col:
            return {"error": "Chart config requires 'x' and 'y' columns"}

        try:
            if group_by and group_by in df.columns:
                chart_data = {}
                for group, group_df in df.groupby(group_by):
                    chart_data[str(group)] = {
                        "x": group_df[x_col].tolist(),
                        "y": group_df[y_col].tolist(),
                    }
            else:
                chart_data = {
                    "x": df[x_col].tolist(),
                    "y": df[y_col].tolist(),
                }

            result = {
                "chart_type": chart_type,
                "x_column": x_col,
                "y_column": y_col,
                "group_by": group_by,
                "data": chart_data,
            }

            if output_path:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt

                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                plt.figure(figsize=(10, 6))
                if group_by and group_by in df.columns:
                    for group, group_df in df.groupby(group_by):
                        plt.plot(group_df[x_col], group_df[y_col], label=str(group), marker="o")
                    plt.legend()
                else:
                    if chart_type == "bar":
                        plt.bar(df[x_col], df[y_col])
                    elif chart_type == "line":
                        plt.plot(df[x_col], df[y_col], marker="o")
                    elif chart_type == "scatter":
                        plt.scatter(df[x_col], df[y_col])

                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.title(config.get("title", f"{y_col} by {x_col}"))
                plt.tight_layout()
                plt.savefig(output_path, dpi=150)
                plt.close()
                result["chart_path"] = output_path

            return result
        except Exception as exc:
            return {"error": str(exc)}

    def filter_rows(
        self,
        rows: List[Dict[str, Any]],
        filter_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if not rows:
            return []

        if not PANDAS_AVAILABLE:
            return self._basic_filter(rows, filter_config)

        df = pd.DataFrame(rows)
        conditions = filter_config.get("conditions", [])

        for condition in conditions:
            column = condition.get("column")
            operator = condition.get("operator", "==")
            value = condition.get("value")

            if column not in df.columns:
                continue

            if operator == "==":
                df = df[df[column] == value]
            elif operator == "!=":
                df = df[df[column] != value]
            elif operator == ">":
                df = df[df[column] > value]
            elif operator == ">=":
                df = df[df[column] >= value]
            elif operator == "<":
                df = df[df[column] < value]
            elif operator == "<=":
                df = df[df[column] <= value]
            elif operator == "contains":
                df = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
            elif operator == "in":
                df = df[df[column].isin(value)]
            elif operator == "not_in":
                df = df[~df[column].isin(value)]

        return df.to_dict(orient="records")

    def _basic_filter(
        self,
        rows: List[Dict[str, Any]],
        filter_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        conditions = filter_config.get("conditions", [])
        filtered = rows
        for condition in conditions:
            column = condition.get("column")
            operator = condition.get("operator", "==")
            value = condition.get("value")
            if operator == "==":
                filtered = [r for r in filtered if r.get(column) == value]
            elif operator == "!=":
                filtered = [r for r in filtered if r.get(column) != value]
            elif operator == "contains":
                filtered = [r for r in filtered if str(value).lower() in str(r.get(column, "")).lower()]
        return filtered