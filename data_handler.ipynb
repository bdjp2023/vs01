# File: data_handler.py
"""
収集データの保存を担うモジュール。

- CSV（output_YYYY-MM-DD.csv）と Excel（output_YYYY-MM-DD.xlsx）の両方を出力する。
- 重複行の除去（任意）と件数ログを行う。
"""

from datetime import date
from pathlib import Path
from typing import Dict, List

import pandas as pd

from constants import get_logger

logger = get_logger()

OUTPUT_DIR = Path("output")


def _build_filename(extension: str) -> Path:
    """
    output_YYYY-MM-DD.<ext> 形式のパスを生成する。

    Args:
        extension: 拡張子（"csv" / "xlsx"）。

    Returns:
        Path: 出力ファイルパス。
    """
    today = date.today().isoformat()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"output_{today}.{extension}"


def save_data(rows: List[Dict[str, str]], drop_duplicates: bool = True) -> None:
    """
    収集データを CSV と Excel の両形式で保存する。

    Args:
        rows: 抽出済みの行データ（辞書のリスト）。
        drop_duplicates: 重複行を除去するか（既定 True）。
    """
    if not rows:
        logger.warning("保存対象データが空です。出力をスキップします。")
        return

    df = pd.DataFrame(rows)

    if drop_duplicates:
        before = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        logger.info("重複除去: %d -> %d 行", before, len(df))

    # CSV 出力（Excel での文字化け防止に utf-8-sig）
    csv_path = _build_filename("csv")
    try:
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info("CSV を出力しました: %s（%d 行）", csv_path, len(df))
    except Exception as exc:
        logger.error("CSV 出力に失敗: %s", exc)

    # Excel 出力
    xlsx_path = _build_filename("xlsx")
    try:
        df.to_excel(xlsx_path, index=False, engine="openpyxl")
        logger.info("Excel を出力しました: %s（%d 行）", xlsx_path, len(df))
    except Exception as exc:
        logger.error("Excel 出力に失敗（openpyxl 未導入の可能性）: %s", exc)