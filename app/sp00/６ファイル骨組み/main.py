# File: main.py
"""
逆順ページネーション対応 ウェブスクレイパー（エントリポイント・完全版）

設計方針:
    - robots.txt の遵守（Disallow パスは即時終了）
    - 人間らしい挙動（三角分布待機・スクロール・マウス移動・ホバー）
    - Playwright Locator を第一優先、BeautifulSoup をフォールバック
    - ブロックページ（Cloudflare/DataDome/PerimeterX）検知時は安全停止
    - 個人情報・ログイン情報は一切取得しない

走査ロジック（逆順）:
    1. jump（最終ページ付近の URL）へ goto
    2. 現在ページを抽出
    3. back（XPath）で1ページ前へ戻る
    4. 2〜3 を繰り返し、戻れなくなった or MAX_PAGES 到達で終了

起動時:
    - check_dependencies() で依存ライブラリの導入状況を確認し、
      必須が欠けていれば分かりやすく案内して終了する。
    - 任意ライブラリ（stealth / fake-useragent / openpyxl）の不足は
      警告のみ表示し、機能制限付きで続行可能とする。

優先度: 安定性 ≧ 検知回避 ＞ 速度／ヘッドレス: なし（ヘッドフル）
"""

import importlib.util
import sys
import logging
import os

# ---------------------------------------------------------------------------
# 依存ライブラリチェック
# ---------------------------------------------------------------------------
# 注意:
#   本ブロックは「重い import を行う前」に実行する必要がある。
#   そのため playwright 等の本体 import は run() 内・関数内で遅延 import せず、
#   check_dependencies() 通過後に行う設計とする（下部の遅延 import を参照）。

# (モジュール名, pip名, 必須かどうか) のリスト
_DEPENDENCIES = [
    ("playwright", "playwright", True),
    ("pandas", "pandas", True),
    ("bs4", "beautifulsoup4", True),
    ("openpyxl", "openpyxl", False),
    ("fake_useragent", "fake-useragent", False),
    ("playwright_stealth", "playwright-stealth", False),
]

def check_dependencies() -> bool:
    """
    依存ライブラリの導入状況を確認する。

    必須ライブラリが欠けている場合は False を返し、
    任意ライブラリの不足は警告のみ表示して継続可能とする。

    Returns:
        bool: 必須がすべて揃っていれば True。
    """
    print("\n--- [DEBUG]１．依存ライブラリのチェック開始 ---")
    missing_required = []
    missing_optional = []

    for module_name, pip_name, required in _DEPENDENCIES:
        if importlib.util.find_spec(module_name) is None:
            if required:
                missing_required.append(pip_name)
            else:
                missing_optional.append(pip_name)
        else:
            print(f"  [OK] {module_name} は導入済みです。")
    # 任意ライブラリの不足は警告のみ（続行可能）
    if missing_optional:
        print("⚠️ 任意ライブラリが未導入です（機能制限あり・続行可能）:")
        for name in missing_optional:
            print(f"   - {name}")
        print(f"   → pip install {' '.join(missing_optional)}")

    # 必須ライブラリの不足は致命的（実行不可）
    if missing_required:
        print("⛔ 必須ライブラリが不足しています。実行できません:")
        for name in missing_required:
            print(f"   - {name}")
        print(f"   → pip install {' '.join(missing_required)}")
        print("   → playwright install chromium  も忘れずに実行してください。")
        return False

    print("--- [DEBUG] 依存ライブラリのチェック完了 ---\n")
    return True


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------
# ヘッドレス指定（ユーザー要望によりヘッドフル）False=なし
HEADLESS = False


def run() -> None:
    """
    スクレイパー全体を実行するメイン処理。

    依存チェックを通過した後に呼ばれる前提のため、本関数内で
    重いライブラリ・自作モジュールを遅延 import する。
    これにより、依存不足時はトレースバックではなく
    check_dependencies() の案内メッセージで安全に終了できる。
    """
    # --- 遅延 import（依存チェック通過後に実行） ---
    from typing import Dict, List
    from playwright.sync_api import sync_playwright

    print("　　[DEBUG]  スクレイピングのインポートを実行...")
    try:
        from browser_utils import (
            apply_stealth,
            check_robots,
            detect_block,
            get_user_agent,
            human_like_behavior,
            human_like_delay,
            wait_for_network_idle,
        )
        from config import extract_su_columns, load_config, setup_logging
        from constants import INPUT_FILE, MAX_PAGES
        from data_handler import save_data
        from scraper_core import (
            extract_page_data,
            navigate_back,
            save_screenshot,
            wait_with_retry,
            scroll_to_bottom,      # 追加
            click_load_more,       # 追加
            wait_for_stable_dom    # 追加
        )
        print("  [OK] インポート成功")
        print(f"  [HINT]  現在のディレクトリ: {os.getcwd()}")
        # ここにあった return は削除しました（戻ってしまうと以下の処理が動かないため）

    except ImportError as e:
        print(f" [ERROR] モジュールの読み込みに失敗しました: {e}")
        return
    except Exception as e:
        print(f" [ERROR] 予期せぬエラーが発生しました: {e}")
        return
        
    # --- ロガー初期化（最初に行う） ---
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("スクレイパーを開始します。")

    # --- 設定読み込み ---
    print(f"\n--- [DEBUG] ３．設定ファイル読み込み開始:{INPUT_FILE} ---")
    if not os.path.exists(INPUT_FILE):
        print(f"  [ERROR]  入力ファイルが見つかりません: {os.path.abspath(INPUT_FILE)}")
        return
        
    try:  # tey から try に修正
        config = load_config(INPUT_FILE)
        print(f"  [OK]  入力データを取得しました。キー一覧: {list(config.keys())}")
        
        hp = config.get("hp", "")
        jump = config.get("jump", "")
        back_selector = config.get("back", "")
        columns = extract_su_columns(config)

        logger.info("hp   : %s", hp)
        logger.info("jump : %s", jump)
        logger.info("back : %s", back_selector)
        logger.info("有効セレクター数: %d 個", len(columns))

        print(f"  [DEBUG] hp: {hp}")
        print(f"  [DEBUG] jump: {jump}")
        print(f"  [DEBUG] back_selector: {back_selector}")
        print(f"  [DEBUG] columns: {columns}")

        logger.info("有効セレクター数: %d 個", len(columns))
    except Exception as e:
        print(f" [ERROR] 入力項目読み込み中の例外エラー発生: {e}")
        return

    # --- 必須設定の検証 ---
    if not jump:
        print("jump（開始URL）が未設定です。終了します。")
        logger.error("jump（開始URL）が未設定です。終了します。")
        return
    if not columns:
        print("抽出セレクター（su*）が1つもありません。終了します。")
        logger.error("抽出セレクター（su*）が1つもありません。終了します。")
        return


    user_agent = get_user_agent()

    # --- robots.txt チェック（Disallow なら即終了） ---
    base_for_robots = hp or jump
    print("fーーー[DEBUG]　4. robots.txt チェック実行中...(Target: {base_for_robots}) ---")
    if not check_robots(base_for_robots, jump, user_agent):
        logger.error("robots.txt により  Disallow のため終了します。")
        return
    print("  [OK] robots.txt チェック通過しました。")

    all_rows: List[Dict[str, str]] = []

# --- Playwright 起動 ---
    print("\n--- [DEBUG] ５．Playweight ブラウザの起動 ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1366, "height": 900},
            locale="ja-JP",
        )
        page = context.new_page()
        apply_stealth(page)  # Stealth 適用

        try:
            # 開始ページへ遷移
            print(f"  [DEBUG] 開始ページに移管します。")
            logger.info("開始ページへ遷移します: %s", jump)
            page.goto(jump, wait_until="domcontentloaded", timeout=150)
            wait_for_network_idle(page)
            print(f"  [OK] 開始ページに移動しました。現在のURL: {page.url}")


            # 判定用にループ外で変数を初期化
            page_no = 0

            # --- 逆順ページングループ（MAX_PAGES 上限） ---
            for page_no in range(1, MAX_PAGES + 1):
                print(f"\n--- [PAGE {page_no}/{MAX_PAGES}]")
                logger.info("-" * 50)
                logger.info(
                    "ページ %d / 最大 %d を処理中: %s",
                    page_no, MAX_PAGES, page.url,
                )

                # ブロック検知 → 安全停止
                if detect_block(page):
                    print("  [CRITICAL] **ブロックを検知しました ")
                    logger.error("ブロックを検知したため安全停止します。")
                    save_screenshot(page, f"blocked_page_{page_no}")
                    break

                # 基準列の出現を待機
                base_selector = next(iter(columns.values()))
                print(f"  [DEBUG] 要素抽出中: {base_selector}")
                if not wait_with_retry(page, base_selector):
                    print("  [WARN] 基準要素がありません。")
                    logger.warning("基準要素が出現しませんでした。スキップします。")
                    save_screenshot(page, f"no_element_page_{page_no}")

                # 人間らしい挙動
                human_like_behavior(page)

                # --- 動的ロード方式に応じた処理 ---
                # paging_mode は設定から取得（将来的な拡張用として保持）
                paging_mode = config.get("paging_mode", "reverse")

                if config.get("infinite_scroll"):
                    # 無限スクロールの場合
                    total = scroll_to_bottom(page, base_selector)
                    logger.info("無限スクロール完了: %d 件をロード", total)
                
                elif config.get("load_more_selector"):
                    # 「もっと見る」ボタンがある場合
                    clicks = click_load_more(page, config["load_more_selector"])
                    logger.info("「もっと見る」を %d 回クリック", clicks)
                
                else:
                    # 通常のページ遷移の場合、DOMが安定するのを待つ
                    wait_for_stable_dom(page, base_selector, timeout=8.0)
                # データ抽出
                rows = extract_page_data(page, columns)
                if rows:
                    print(f" [OK] {len(rows)} 件のデータを抽出しました。")
                    all_rows.extend(rows)
                    logger.info("累計収集行数: %d 行", len(all_rows))
                else:
                    print(" [WARN] データの抽出に失敗しました。{len(rows)} 件目のデータ")
                    logger.warning("このページからデータを取得できませんでした。")

                # 人間らしい待機
                human_like_delay()

                # 前ページへ戻る（戻れなければループ終了）
                print("  [DEBUG] ページ戻り。")
                if not navigate_back(page, back_selector):
                    print("  [INFO] 戻るボタンが押せなくなりました終了します。")
                    logger.info("これ以上戻れないため走査を終了します。")
                    break

                wait_for_network_idle(page)

            # --- ループ終了後の判定 ---
            # ループ変数が MAX_PAGES に達しており、かつ break していない場合
            if page_no >= MAX_PAGES:
                logger.warning(
                    "MAX_PAGES(%d) に到達したため終了します。", MAX_PAGES
                )

        except Exception as exc:
            print(f"  [FATAL ERROR]メインループで予期せぬ例外:\n{exc}")
            logger.error("メインループで予期せぬ例外: %s", exc)
            save_screenshot(page, "fatal_error")
        finally:
            # --- 後始末と保存 ---
            print("\n--- [DEBUG] ６． 最終処理 ---")
            print(f"  [INFO] 総収集 件数: {len(all_rows)}") # all_lows から修正
            logger.info("=" * 60)
            logger.info("走査終了。総収集行数: %d 行", len(all_rows))
            save_data(all_rows)
            # --- プレビュー ---
            if all_rows:
                print(" [PREVIEW] 取得データの戦闘5件:")
                for r in all_rows[:5]:
                    print(f"    {r}")

            context.close()
            browser.close()
            logger.info("ブラウザを閉じました。処理完了。")

            # main.py の末尾にこれが必要です
if __name__ == "__main__":
    print("=== デバッグモード開始 ===")
    if check_dependencies():
        run()
    print("=== デバッグモード終了 ===")
