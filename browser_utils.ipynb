# File: browser_utils.py
"""
ブラウザ操作の低レベルユーティリティ。（デバッグ修正版）

修正点:
    - Bug2: wait_for_network_idle のデフォルトを load 状態優先＋短縮タイムアウトに。
            networkidle で固まるサイト向けに load フォールバックを追加。
    - Bug3: human_like_behavior の hover を可視要素に限定し timeout を短縮、
            要素取得を軽量化。
"""

import random
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from playwright.sync_api import Locator, Page

from constants import (
    BLOCK_SIGNATURES,
    WAIT_MAX,
    WAIT_MIN,
    WAIT_MODE,
    get_logger,
)

logger = get_logger()

# ---------------------------------------------------------------------------
# Playwright Stealth の安全な取り込み
# ---------------------------------------------------------------------------
_STEALTH_AVAILABLE = False
_stealth_sync = None
try:
    from playwright_stealth import stealth_sync as _stealth_sync  # 旧API

    _STEALTH_AVAILABLE = True
except Exception:  # pragma: no cover
    try:
        from playwright_stealth import Stealth as _StealthClass  # 新API

        def _stealth_sync(page: Page) -> None:
            """新API（Stealthクラス）を旧API互換の関数として包む。"""
            _StealthClass().apply_stealth_sync(page)

        _STEALTH_AVAILABLE = True
    except Exception:
        _STEALTH_AVAILABLE = False


try:
    from fake_useragent import UserAgent

    _UA = UserAgent()
except Exception:  # pragma: no cover
    _UA = None

_FALLBACK_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def get_user_agent() -> str:
    """ランダムな User-Agent を返す（失敗時は固定 UA）。"""
    if _UA is not None:
        try:
            return _UA.random
        except Exception:
            pass
    return _FALLBACK_UA


def apply_stealth(page: Page) -> None:
    """ページに Stealth を適用する（利用可能な場合のみ）。"""
    if _STEALTH_AVAILABLE and _stealth_sync is not None:
        try:
            _stealth_sync(page)
            logger.info("Playwright Stealth を適用しました。")
        except Exception as exc:
            logger.warning("Stealth 適用に失敗（継続）: %s", exc)
    else:
        logger.warning("playwright_stealth が未導入のため Stealth を適用しません。")


def to_locator(page: Page, selector: str) -> Locator:
    """
    セレクターが XPath か CSS かを自動判別して Locator を返す。

    Args:
        page: 対象ページ。
        selector: CSS または XPath。

    Returns:
        Locator: 対応する Locator。
    """
    s = selector.strip()
    if s.startswith("xpath="):
        return page.locator(s)
    if s.startswith("//") or s.startswith("/") or s.startswith("("):
        return page.locator(f"xpath={s}")
    return page.locator(s)


def check_robots(base_url: str, target_url: str, user_agent: str) -> bool:
    """
    robots.txt を取得・解析し target_url の可否を返す（取得失敗時は許可）。

    Args:
        base_url: ドメイン判定基準 URL。
        target_url: 可否確認対象 URL。
        user_agent: 判定用 User-Agent。

    Returns:
        bool: アクセス可なら True。
    """
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    parser = RobotFileParser()
    parser.set_url(robots_url)

    try:
        parser.read()
        logger.info("robots.txt を取得しました: %s", robots_url)
    except Exception as exc:
        logger.warning(
            "robots.txt を取得できませんでした（%s）。続行しますが注意。", exc
        )
        return True

    allowed = parser.can_fetch(user_agent, target_url)
    if allowed:
        logger.info("robots.txt によりアクセス許可: %s", target_url)
    else:
        logger.warning("robots.txt により Disallow: %s", target_url)
    return allowed


def human_like_delay() -> None:
    """5〜18秒の三角分布（最頻 9 秒）でランダム待機する。"""
    wait = random.triangular(WAIT_MIN, WAIT_MAX, WAIT_MODE)
    logger.info("待機: %.2f 秒", wait)
    time.sleep(wait)


def human_like_behavior(page: Page) -> None:
    """
    ランダムスクロール・マウス移動・ホバーで自動化を悟られにくくする。

    修正: hover は可視要素に限定し timeout を短縮、要素取得を軽量化。

    Args:
        page: 対象ページ。
    """
    try:
        viewport = page.viewport_size or {"width": 1280, "height": 800}
        width = viewport["width"]
        height = viewport["height"]

        # ランダムな複数回スクロール（遅延ロード促進）
        for _ in range(random.randint(2, 5)):
            delta = random.randint(200, 800)
            page.mouse.wheel(0, delta)
            time.sleep(random.uniform(0.4, 1.4))

        # 軽いマウス移動
        for _ in range(random.randint(1, 3)):
            x = random.randint(0, max(1, width - 1))
            y = random.randint(0, max(1, height - 1))
            page.mouse.move(x, y, steps=random.randint(5, 20))
            time.sleep(random.uniform(0.2, 0.8))

        # 可視リンクへのホバー（先頭付近のみ・短timeout）
        try:
            links = page.locator("a:visible")
            count = min(links.count(), 10)  # 全件 all() せず軽量化
            if count > 0:
                idx = random.randint(0, count - 1)
                links.nth(idx).hover(timeout=1500)
                time.sleep(random.uniform(0.3, 1.0))
        except Exception:
            pass

    except Exception as exc:
        logger.debug("人間らしい挙動の一部に失敗（無視）: %s", exc)


def detect_block(page: Page) -> bool:
    """
    Cloudflare/DataDome/PerimeterX 等のブロックページを検知する。

    Args:
        page: 対象ページ。

    Returns:
        bool: ブロックと判定したら True。
    """
    try:
        title = (page.title() or "").lower()
        body_text = ""
        try:
            body_text = (page.inner_text("body", timeout=3000) or "").lower()
        except Exception:
            pass

        haystack = f"{title} {body_text[:2000]}"
        for sig in BLOCK_SIGNATURES:
            if sig in haystack:
                logger.error(
                    "ブロックページを検知（シグネチャ: '%s', title: '%s'）",
                    sig, title,
                )
                return True
    except Exception as exc:
        logger.debug("ブロック検知中の例外（無視）: %s", exc)
    return False


def wait_for_network_idle(page: Page, timeout: int = 10000) -> None:
    """
    ページの読み込み安定を待つ。

    修正: networkidle で固まるサイト向けに、まず load を待ち、
    短いタイムアウトで networkidle を試す（失敗してもログのみで継続）。

    Args:
        page: 対象ページ。
        timeout: networkidle 試行のタイムアウト（ミリ秒、短め）。
    """
    # まず load を確実に待つ（多くのサイトで十分）
    try:
        page.wait_for_load_state("load", timeout=timeout)
    except Exception as exc:
        logger.debug("load 待機タイムアウト（無視）: %s", exc)

    # 続けて networkidle を短時間だけ試す（固まるサイト対策で短縮）
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception as exc:
        logger.debug("networkidle 待機タイムアウト（無視して継続）: %s", exc)
