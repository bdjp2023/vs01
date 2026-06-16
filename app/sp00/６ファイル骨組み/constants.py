# File: constants.py
"""
プロジェクト全体で共有する定数とロガー取得関数を定義するモジュール。

- 入出力ファイル名、上限ページ数、待機パラメータ、ブロック検知シグネチャを集約する。
- ロガーの実体は config.py の setup_logging() で構築し、本モジュールの
  get_logger() は構築済みロガーを取得するだけの薄いヘルパーとして機能する。
"""

import logging
from logging import Logger

# ====================== ファイル関連 ======================
INPUT_FILE = "inputizm.json"        # 設定ファイル（配列の先頭要素を使用）
LOG_FILE = "scrape.log"             # ログ出力先

# ====================== 走査制御 ======================
# 無限ループ防止の安全弁。逆順走査でも本上限を超えたら強制終了する。
MAX_PAGES = 50

# ====================== ブロックページ検知 ======================
# タイトル/本文に含まれ得る、反ボットサービス由来の文字列群。
BLOCK_SIGNATURES = [
    "cloudflare",
    "attention required",
    "checking your browser",
    "datadome",
    "perimeterx",
    "px-captcha",
    "access denied",
    "verify you are human",
    "just a moment",
    "403 Forbidden",
    "Access Denied",
    "ロボットではありません",
    "一時的にアクセスを制限"
]

# ====================== 人間らしい待機（三角分布） ======================
# random.triangular(low, high, mode) に渡すパラメータ。
WAIT_MIN = 5.0
WAIT_MAX = 18.0
WAIT_MODE = 9.0


def get_logger(name: str = "scraper") -> Logger:
    """
    構築済みロガーを取得する。

    実際のハンドラ設定は config.setup_logging() が行う。本関数は
    どのモジュールからでも同一ロガーを参照できるようにするための窓口。

    Args:
        name: ロガー名（既定 "scraper"）。

    Returns:
        logging.Logger: 取得したロガー。
    """
    return logging.getLogger(name)
