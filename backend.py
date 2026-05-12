"""
Backend logic for Retail / E-commerce Sales Dashboard.
This file contains only Python code for:
- loading the given CSV datasets
- cleaning and standardizing columns
- creating Andhra Pradesh city names
- filtering data
- preparing KPI and chart data
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_FILES = [
    BASE_DIR / "sales_data.csv",
    BASE_DIR / "retail_sales.csv",
]

AP_CITY_MAP = {
    "North": "Visakhapatnam",
    "South": "Nellore",
    "East": "Vijayawada",
    "West": "Kurnool",
    "Not Available": "Tirupati",
    "Unknown": "Tirupati",
}

FALLBACK_AP_CITIES = [
    "Nellore",
    "Vijayawada",
    "Visakhapatnam",
    "Guntur",
    "Tirupati",
    "Kurnool",
    "Rajahmundry",
    "Anantapur",
    "Kadapa",
    "Ongole",
]


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    return df


def _assign_city(df: pd.DataFrame) -> pd.Series:
    """Create AP city names from existing region values or product/category pattern."""
    region_city = df["Region"].astype(str).map(AP_CITY_MAP)

    fallback_index = (pd.factorize(df["Product"].astype(str) + "_" + df["Category"].astype(str))[0]) % len(FALLBACK_AP_CITIES)
    fallback_city = pd.Series([FALLBACK_AP_CITIES[i] for i in fallback_index], index=df.index)

    return region_city.fillna(fallback_city)


def _standardize_dataset(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Convert different dataset formats into one common dashboard structure."""
    df = _clean_columns(df)

    if "Order_Date" in df.columns and "Date" not in df.columns:
        df = df.rename(columns={"Order_Date": "Date"})

    required_defaults = {
        "Order_ID": np.nan,
        "Category": "Unknown",
        "Product": "Unknown",
        "Region": "Not Available",
        "Quantity": 1,
        "Price": np.nan,
        "Sales": 0,
        "Date": pd.NaT,
    }

    for col, default_value in required_defaults.items():
        if col not in df.columns:
            df[col] = default_value

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(1)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    missing_price = df["Price"].isna() & df["Quantity"].ne(0)
    df.loc[missing_price, "Price"] = df.loc[missing_price, "Sales"] / df.loc[missing_price, "Quantity"]

    df["City"] = _assign_city(df)
    df["Source"] = source_name

    final_columns = [
        "Order_ID",
        "Date",
        "Category",
        "Product",
        "City",
        "Quantity",
        "Price",
        "Sales",
        "Source",
    ]

    df = df[final_columns]
    df = df.dropna(subset=["Date", "Sales", "Product", "Category", "City"])
    df = df[df["Sales"] >= 0]
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def load_sales_data(files: Iterable[Path] | None = None) -> pd.DataFrame:
    """Load and combine all available CSV datasets."""
    files = list(files or DATA_FILES)
    frames: list[pd.DataFrame] = []

    for file_path in files:
        if file_path.exists():
            raw_df = pd.read_csv(file_path)
            frames.append(_standardize_dataset(raw_df, file_path.stem))

    if not frames:
        raise FileNotFoundError("No sales CSV files found. Keep sales_data.csv and retail_sales.csv in the project folder.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates()
    return combined


def filter_data(
    df: pd.DataFrame,
    categories: list[str] | None = None,
    products: list[str] | None = None,
    cities: list[str] | None = None,
    sources: list[str] | None = None,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    data = df.copy()

    if categories:
        data = data[data["Category"].isin(categories)]
    if products:
        data = data[data["Product"].isin(products)]
    if cities:
        data = data[data["City"].isin(cities)]
    if cities:
        data = data[data["City"].isin(cities)]    
    if start_date is not None:
        data = data[data["Date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        data = data[data["Date"] <= pd.to_datetime(end_date)]

    return data.reset_index(drop=True)


def get_kpis(df: pd.DataFrame) -> dict[str, float]:
    total_sales = float(df["Sales"].sum())
    total_orders = int(len(df))
    total_quantity = int(df["Quantity"].sum())
    avg_order_value = float(df["Sales"].mean()) if total_orders else 0.0

    return {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_quantity": total_quantity,
        "avg_order_value": avg_order_value,
    }


def top_products_by_sales(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    return (
        df.groupby("Product", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(limit)
    )


def bottom_products_by_sales(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    return (
        df.groupby("Product", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=True)
        .head(limit)
    )


def sales_by_category(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)


def sales_by_city(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("City", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)


def sales_trend(df: pd.DataFrame, freq: str = "ME") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Date", "Sales"])

    return df.set_index("Date").resample(freq)["Sales"].sum().reset_index()


def choose_trend_frequency(start_date, end_date) -> str:
    days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
    if days > 365:
        return "ME"
    if days > 60:
        return "W"
    return "D"
