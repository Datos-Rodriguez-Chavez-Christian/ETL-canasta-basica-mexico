from pathlib import Path
from datetime import datetime
import pandas as pd

from config import OUTPUT_COLUMNS, OUTPUT_DIR, SUMMARY_COLUMNS
from utils import ensure_directories

def export_products(store_key: str, products: list[dict]) -> Path:
    ensure_directories()
    fecha_archivo = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"productos_{store_key}_{fecha_archivo}.csv"
    output_path = OUTPUT_DIR / nombre_archivo
    df = pd.DataFrame(products)

    for column in OUTPUT_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[OUTPUT_COLUMNS]
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path

def export_summary(summary_rows: list[dict]) -> Path:
    ensure_directories()

    summary_path = OUTPUT_DIR / "scraping_summary.csv"
    df = pd.DataFrame(summary_rows)

    for column in SUMMARY_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[SUMMARY_COLUMNS]

    write_header = not summary_path.exists()
    df.to_csv(
        summary_path,
        mode="a",
        header=write_header,
        index=False,
        encoding="utf-8-sig",
    )
    return summary_path