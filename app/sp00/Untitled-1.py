# %%
# File: main.py
import nest_asyncio
nest_asyncio.apply()

import importlib.util
import sys
import logging
import os

# --- 依存関係の定義 ---
_DEPENDENCIES = [
    ("playwright", "playwright", True),
    ("pandas", "pandas", True),
    ("bs4", "beautifulsoup4", True),
    ("openpyxl", "openpyxl", False),
    ("fake_useragent", "fake-useragent", False),
    ("playwright_stealth", "playwright-stealth", False),
]

def check_dependencies() -> bool:
    print("\n--- [DEBUG] 1. 依存ライブラリのチェック開始 ---")
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

    if missing_optional:
        print(f"  [INFO] 任意ライブラリ不足: {missing_optional}")

    if missing_required:
        print(f"  [ERROR] 必須ライブラリ不足: {missing_required}")
        return False
    
    print("--- [DEBUG] 依存ライブラリのチェック完了 ---\n")
    return True

HEADLESS = False

def run() -> None:
    print("--- [DEBUG] 2. run() 関数を開始しました ---")
    
    # --- 必要なモジュールのインポート ---
    from typing import Dict, List
    from playwright.sync_api import sync_playwright

    print("  [DEBUG] モジュールのインポートを試みます...")
    try:
        from browser_utils import (
            apply_stealth, check_robots, detect_block, get_user_agent,
            human_like_behavior, human_like_delay, wait_for_network_idle,
        )
        from config import extract_su_columns, load_config, setup_logging
        from constants import INPUT_FILE, MAX_PAGES
        from data_handler import save_data
        from scraper_core import (
            extract_page_data, navigate_back, save_screenshot, wait_with_retry,
        )
        print("  [OK] 全ての自作モジュールのインポートに成功しました。")
    except ImportError as e:
        print(f"  [ERROR] インポート失敗: {e}")
        print(f"  [HINT] 現在の作業ディレクトリ: {os.getcwd()}")
        return

    # --- ロガー初期化 ---
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("スクレイパーを開始します。")

    # --- 設定読み込み ---
    print(f"\n--- [DEBUG] 3. 設定ファイル読み込み開始: {INPUT_FILE} ---")
    if not os.path.exists(INPUT_FILE):
        print(f"  [ERROR] ファイルが見つかりません: {os.path.abspath(INPUT_FILE)}")
        return

    try:
        config = load_config(INPUT_FILE)
        print(f"  [OK] configデータを取得しました。キー一覧: {list(config.keys())}")
        
        hp = config.get("hp", "")               
        jump = config.get("jump", "")           
        back_selector = config.get("back", "")  
        columns = extract_su_columns(config)    

        print(f"  [DEBUG] hp: {hp}")
        print(f"  [DEBUG] jump: {jump}")
        print(f"  [DEBUG] back_selector: {back_selector}")
        print(f"  [DEBUG] 抽出カラム: {columns}")
        
        logger.info("有効セレクター数: %d 個", len(columns))
    except Exception as e:
        print(f"  [ERROR] 設定読み込み中に例外発生: {e}")
        return

    # --- 必須設定の検証 ---
    if not jump:
        print("  [ERROR] jump (開始URL) が設定されていません。")
        return
    if not columns:
        print("  [ERROR] 有効な抽出セレクター (su1等) が見つかりません。")
        return

    print("--- [DEBUG] 設定の検証を通過しました ---\n")

    user_agent = get_user_agent()
    base_for_robots = hp or jump
    
    print(f"--- [DEBUG] 4. robots.txt チェック実行中... (Target: {base_for_robots}) ---")
    if not check_robots(base_for_robots, jump, user_agent):
        logger.error("robots.txt により Disallow のため終了します。")
        return
    print("  [OK] robots.txt チェックを通過しました。")

    all_rows: List[Dict[str, str]] = []

    # --- Playwright 起動 ---
    print("\n--- [DEBUG] 5. Playwright ブラウザを起動します ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1366, "height": 900},
            locale="ja-JP",
        )
        page = context.new_page()
        apply_stealth(page)

        try:
            print(f"  [DEBUG] ページ遷移中: {jump}")
            page.goto(jump, wait_until="domcontentloaded", timeout=60000)
            wait_for_network_idle(page)
            print(f"  [OK] ページに到達しました。現在のURL: {page.url}")

            page_no = 0
            for page_no in range(1, MAX_PAGES + 1):
                print(f"\n--- [PAGE {page_no}/{MAX_PAGES}] ---")
                
                if detect_block(page):
                    print("  [CRITICAL] ブロックを検知しました。")
                    save_screenshot(page, f"blocked_page_{page_no}")
                    break

                # 基準列の待機
                base_selector = next(iter(columns.values()))
                print(f"  [DEBUG] 要素待機中: {base_selector}")
                if not wait_with_retry(page, base_selector):
                    print("  [WARN] 基準要素が見つかりませんでした。")
                    save_screenshot(page, f"no_element_page_{page_no}")

                human_like_behavior(page)

                # データ抽出
                rows = extract_page_data(page, columns)
                if rows:
                    print(f"  [OK] {len(rows)} 件のデータを抽出しました。")
                    all_rows.extend(rows)
                else:
                    print("  [WARN] データが抽出されませんでした。")

                human_like_delay()

                # 前ページへ戻る
                print(f"  [DEBUG] 戻るボタンを試行中: {back_selector}")
                if not navigate_back(page, back_selector):
                    print("  [INFO] 戻るボタンが押せない、または存在しません。走査を完了します。")
                    break

                wait_for_network_idle(page)

        except Exception as exc:
            print(f"  [FATAL ERROR] メインループ中に例外が発生しました:\n{exc}")
            save_screenshot(page, "fatal_error")
        finally:
            print("\n--- [DEBUG] 6. 最終処理 ---")
            print(f"  [INFO] 総収集行数: {len(all_rows)}")
            
            # --- プレビュー ---
            if all_rows:
                print("  [PREVIEW] 取得データの先頭3件:")
                for r in all_rows[:3]:
                    print(f"    {r}")

            context.close()
            browser.close()
            print("  [OK] ブラウザを正常に終了しました。")

# --- 実行ブロック ---
if __name__ == "__main__":
    print("=== デバッグモード開始 ===")
    if check_dependencies():
        run()
    else:
        print("=== 必須ライブラリがないため中止しました ===")
    print("=== デバッグモード終了 ===")


