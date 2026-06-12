# File: scraper_core.py
"""
スクレイピングの中核ロジックを提供するモジュール。（デバッグ修正版）

修正点:
    - Bug1: all_text_contents() → all_inner_texts() に修正（存在しないAPIだった）
    - Bug6: BS4 の XPath 判定を to_locator と同基準（//, /, ( ）に統一
    - Locator 経路で空文字を除外し、行数判定を安定化
"""

import time
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from browser_utils import to_locator
from constants import get_logger

logger = get_logger()

SCREENSHOT_DIR = Path("screenshots")


def _is_xpath(selector: str) -> bool:
    """セレクターが XPath か判定する（to_locator と同一基準）。"""
    s = selector.strip()
    return (
        s.startswith("xpath=")
        or s.startswith("//")
        or s.startswith("/")
        or s.startswith("(")
    )


def wait_with_retry(
    page: Page,
    selector: str,
    timeout: int = 15000,
    retries: int = 3,
) -> bool:
    """
    要素が出現するまでリトライ付きで待機する（指数バックオフ）。

    Args:
        page: 対象ページ。
        selector: CSS または XPath セレクター。
        timeout: 1試行あたりのタイムアウト（ミリ秒）。
        retries: 最大リトライ回数。

    Returns:
        bool: 出現を確認できたら True。
    """
    for attempt in range(1, retries + 1):
        try:
            locator = to_locator(page, selector)
            locator.first.wait_for(state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            backoff = 2 ** (attempt - 1)
            logger.warning(
                "要素待機失敗（%d/%d）: %s ／ %d 秒後に再試行",
                attempt, retries, selector, backoff,
            )
            time.sleep(backoff)
        except Exception as exc:
            logger.warning("要素待機中の予期せぬ例外: %s", exc)
            time.sleep(1)
    logger.error("要素待機に最終的に失敗: %s", selector)
    return False


def _extract_with_locator(page: Page, columns: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Playwright Locator を用いて全行のデータを抽出する（第一優先経路）。

    Args:
        page: 対象ページ。
        columns: {列名: セレクター} 辞書。

    Returns:
        list[dict]: 抽出した行データのリスト。
    """
    column_texts: Dict[str, List[str]] = {}
    for col, selector in columns.items():
        try:
            locator = to_locator(page, selector)
            # 修正: all_text_contents() は存在しない → all_inner_texts()
            texts = locator.all_inner_texts()
            column_texts[col] = [t.strip() for t in texts]
        except Exception as exc:
            logger.warning("列 %s の取得に失敗（空で継続）: %s", col, exc)
            column_texts[col] = []

    # su1 を基準に行数を決定（無ければ最大長を採用）
    base_col = next(iter(columns), None)
    if base_col and column_texts.get(base_col):
        row_count = len(column_texts[base_col])
    else:
        row_count = max((len(v) for v in column_texts.values()), default=0)

    rows: List[Dict[str, str]] = []
    for i in range(row_count):
        row = {
            col: (texts[i] if i < len(texts) else "")
            for col, texts in column_texts.items()
        }
        rows.append(row)
    return rows


def _extract_with_bs4(html: str, columns: Dict[str, str]) -> List[Dict[str, str]]:
    """
    BeautifulSoup を用いて全行のデータを抽出する（フォールバック経路）。

    注意: XPath は BeautifulSoup では扱えないためスキップする。

    Args:
        html: ページの HTML。
        columns: {列名: セレクター} 辞書。

    Returns:
        list[dict]: 抽出した行データのリスト。
    """
    soup = BeautifulSoup(html, "html.parser")
    column_texts: Dict[str, List[str]] = {}

    for col, selector in columns.items():
        # 修正: XPath 判定を to_locator と同基準に統一
        if _is_xpath(selector):
            logger.warning("BS4 では XPath を扱えないため列 %s をスキップ", col)
            column_texts[col] = []
            continue
        try:
            elements = soup.select(selector)
            column_texts[col] = [el.get_text(strip=True) for el in elements]
        except Exception as exc:
            logger.warning("BS4 で列 %s の取得に失敗: %s", col, exc)
            column_texts[col] = []

    base_col = next(iter(columns), None)
    if base_col and column_texts.get(base_col):
        row_count = len(column_texts[base_col])
    else:
        row_count = max((len(v) for v in column_texts.values()), default=0)

    rows: List[Dict[str, str]] = []
    for i in range(row_count):
        row = {
            col: (texts[i] if i < len(texts) else "")
            for col, texts in column_texts.items()
        }
        rows.append(row)
    return rows


def extract_page_data(page: Page, columns: Dict[str, str]) -> List[Dict[str, str]]:
    """
    現在のページから全行分のデータを抽出する。

    まず Playwright Locator で抽出を試み、空または例外時は BS4 へフォールバック。

    Args:
        page: 対象ページ。
        columns: {列名: セレクター} 辞書。

    Returns:
        list[dict]: 抽出した行データのリスト。
    """
    if not columns:
        logger.warning("抽出対象の列がありません。")
        return []

    try:
        rows = _extract_with_locator(page, columns)
        if rows:
            logger.info("Locator で %d 行を抽出しました。", len(rows))
            return rows
        logger.info("Locator 抽出が空のため BS4 にフォールバックします。")
    except Exception as exc:
        logger.warning("Locator 抽出で例外（BS4 へフォールバック）: %s", exc)

    try:
        html = page.content()
        rows = _extract_with_bs4(html, columns)
        logger.info("BS4 で %d 行を抽出しました。", len(rows))
        return rows
    except Exception as exc:
        logger.error("BS4 抽出にも失敗しました: %s", exc)
        return []


def navigate_back(page: Page, back_selector: str, timeout: int = 15000) -> bool:
    """
    「前ページ」リンク（XPath/CSS）をクリックして1ページ戻る。

    戻り先リンクが無い（最初のページ）場合は False を返し、終了条件とする。

    Args:
        page: 対象ページ。
        back_selector: 戻るリンクのセレクター（XPath または CSS）。
        timeout: 要素待機のタイムアウト（ミリ秒）。

    Returns:
        bool: 遷移成功なら True、戻れない場合は False。
    """
    if not back_selector:
        logger.warning("back セレクターが未設定のため戻れません。")
        return False

    try:
        locator = to_locator(page, back_selector)

        # 存在確認（最初のページには無い → 終了条件）
        if locator.count() == 0:
            logger.info("戻るリンクが見つかりません（最初のページと判断）。")
            return False

        try:
            locator.first.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            logger.info("戻るリンクが可視化されません（終了条件と判断）。")
            return False

        prev_url = page.url
        # クリックと遷移完了を expect_navigation で確実に待つ
        try:
            with page.expect_navigation(
                wait_until="domcontentloaded", timeout=timeout
            ):
                locator.first.click()
        except PlaywrightTimeoutError:
            # ナビゲーションが検知できなくても URL 変化で判断
            logger.warning("expect_navigation がタイムアウト（URL で確認）。")

        logger.info("前ページへ遷移: %s -> %s", prev_url, page.url)
        # URL が変わっていなければ失敗とみなす
        if page.url == prev_url:
            logger.info("URL が変化しないため、これ以上戻れないと判断。")
            return False
        return True

    except Exception as exc:
        logger.error("navigate_back で予期せぬ例外: %s", exc)
        return False


def save_screenshot(page: Page, name: str) -> None:
    """
    スクリーンショットを screenshots/ 配下へ保存する（失敗は無視）。

    Args:
        page: 対象ページ。
        name: ファイル名（拡張子不要）。
    """
    try:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOT_DIR / f"{name}.png"
        page.screenshot(path=str(path), full_page=True)
        logger.info("スクリーンショットを保存: %s", path)
    except Exception as exc:
        logger.warning("スクリーンショット保存に失敗（無視）: %s", exc)
