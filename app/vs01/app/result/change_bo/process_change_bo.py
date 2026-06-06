# File: process_change_bo.py
import pandas as pd
from datetime import datetime
from pathlib import Path
from rapidfuzz import process, fuzz

def process_product_to_model(
    acquired_file: str = "acquired_data.csv",
    master_file: str = "master_data.csv",
    output_dir: str = "result/change_bo",
    similarity_threshold: int = 75,   # 類似度75%以上を候補とする
    max_candidates: int = 5           # 最大表示候補数
):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%m_%d")
    end_file = Path(output_dir) / f"{date_str}_end.json"
    check_file = Path(output_dir) / f"{date_str}_check.csv"
    
    acquired = pd.read_csv(acquired_file)
    master = pd.read_csv(master_file)
    
    # マスタをリスト化（ファジー検索用）
    master_items = master['品名'].astype(str).str.strip().tolist()
    master_dict = dict(zip(master['品名'].astype(str).str.strip(), 
                          master['型番'].astype(str).str.strip()))
    
    results = []
    end_list = []
    
    for _, row in acquired.iterrows():
        original_name = str(row['品名']).strip()
        price = row.get('価格', 0)
        
        if pd.isna(price) or price == '':
            price = 0
        else:
            try:
                price = int(float(price))
            except:
                price = 0
        
        # 1. 完全一致チェック
        model = master_dict.get(original_name)
        if model and str(model).strip() != "":
            status = "OK"
            model_value = str(model).strip()
            remark = ""
            end_list.append({"model": model_value, "price": price})
        else:
            # 2. ファジー一致検索
            matches = process.extract(
                original_name, 
                master_items, 
                scorer=fuzz.token_sort_ratio,
                limit=max_candidates
            )
            
            candidates = []
            for match_name, score, _ in matches:
                if score >= similarity_threshold:
                    model_no = master_dict.get(match_name, "")
                    candidates.append(f"{model_no}({score}%)")
            
            if candidates:
                status = "CHECK"
                model_value = ""
                remark = "類似候補: " + ", ".join(candidates)
            else:
                status = "NG"
                model_value = ""
                remark = "該当候補なし"
        
        results.append({
            "取得品名": original_name,
            "型番": model_value,
            "価格": price,
            "判定": status,
            "備考": remark
        })
    
    # 出力
    pd.DataFrame(end_list).to_json(
        end_file, orient="records", force_ascii=False, indent=2
    )
    
    check_df = pd.DataFrame(results)
    check_df.to_csv(check_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ 処理完了 ({date_str})")
    print(f"   完全一致（end.json） : {len(end_list)}件")
    print(f"   要確認・修正用       : {len(results)}件 → {check_file.name}")
    print(f"\n※ check.csv の「判定=CHECK」の行は、備考欄の類似候補を確認して「型番」列を修正してください。")
    
    return check_df


if __name__ == "__main__":
    process_product_to_model()