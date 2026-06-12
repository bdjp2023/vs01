# File: config.py
"""
ロギング設定・設定ファイル読み込み・セレクター抽出を担うモジュール。

統合方針:
    - 提供された2種類の load_config のうち、ログ出力対応版を採用し、
      型チェック・空配列チェックを加えて堅牢化した。
    - logger は basicConfig 版を破棄し、setup_logging() に一本化した。
    - セレクターは手書き dict（active_selectors）を破棄し、
      正規表現＋数値ソートの extract_su_columns() に統一した。
    - su3〜su6 のような空文字列セレクターは自動的に無視される（ユーザー要望）。
"""

import json
import logging
import re
import sys
from logging import Logger
from typing import Any, Dict

from constants import INPUT_FILE, LOG_FILE


def setup_logging(level: int = logging.INFO) -> Logger:
    """
    ファイルとコンソール双方へ出力するロガーを構築する。

    二重登録を防止するため、既にハンドラが設定済みの場合は
    そのまま既存ロガーを返す。

    Args:
        level: ログレベル（既定 logging.INFO）。

    Returns:
        logging.Logger: 設定済みロガー。
    """
    logger = logging.getLogger("scraper")
    logger.setLevel(level)

    # ハンドラの二重登録防止（複数回呼ばれても安全）
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ファイル出力ハンドラ
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # コンソール出力ハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def load_config(path: str = INPUT_FILE) -> Dict[str, Any]:
    """
    設定ファイル（JSON配列）を読み込み、先頭要素（index 0）を返す。

    堅牢化ポイント:
        - FileNotFoundError / JSONDecodeError を個別に握ってログ出力。
        - 配列でない、または空配列の場合は ValueError を送出。

    Args:
        path: 設定ファイルパス（既定 INPUT_FILE）。

    Returns:
        dict: 設定辞書（配列の先頭要素）。

    Raises:
        FileNotFoundError: ファイルが存在しない場合。
        json.JSONDecodeError: JSON が不正な場合。
        ValueError: 配列でない、または空配列の場合。
    """
    logger = logging.getLogger("scraper")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error("設定ファイルが見つかりません: %s", path)
        raise
    except json.JSONDecodeError as exc:
        logger.error("設定ファイルのJSON解析に失敗しました: %s", exc)
        raise

    # 配列かつ非空であることを保証
    if not isinstance(data, list) or not data:
        raise ValueError("inputizm.json は要素を1つ以上含む配列である必要があります。")

    config = data[0]
    if not isinstance(config, dict):
        raise ValueError("配列の先頭要素はオブジェクト（辞書）である必要があります。")

    logger.info("設定を読み込みました（配列 index 0 を使用）: %s", path)
    return config


def extract_su_columns(config: Dict[str, Any]) -> Dict[str, str]:
    """
    「su」+数字（su1, su2, ...）のキーのみを抽出する。

    値（セレクター）が空文字列・空白のみ・非文字列のものは無視する。
    これにより su3〜su6 のような未使用列は自動的に除外される。
    返り値はキー名の数値部分でソートし、列順を安定させる。

    Args:
        config: load_config() が返した設定辞書。

    Returns:
        dict: {列名: セレクター文字列} の辞書（数値昇順）。
    """
    logger = logging.getLogger("scraper")
    su_pattern = re.compile(r"^su(\d+)$")
    selected: Dict[str, str] = {}

    for key, value in config.items():
        match = su_pattern.match(key)
        if not match:
            continue
        # 空文字列・空白のみ・非文字列はスキップ（柔軟な空白無視）
        if not isinstance(value, str) or value.strip() == "":
            continue
        selected[key] = value.strip()

    # キーの数値部分でソートして列順を安定させる
    ordered = dict(
        sorted(
            selected.items(),
            key=lambda kv: int(su_pattern.match(kv[0]).group(1)),
        )
    )
    logger.info("抽出対象の列: %s", list(ordered.keys()))
    return ordered
