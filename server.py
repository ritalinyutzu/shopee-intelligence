import pandas as pd
import numpy as np
import re
import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 配置檔案名稱
CSV_FILE = '海鷹TOP5000關鍵字_20260427_152939.csv'
OUTPUT_JSON = 'weekly_report.json'

def run_analysis_pipeline():
    print(f"--- 啟動階段 2：避強擊弱 AI 分析模式 ---")
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ 錯誤：找不到檔案 {CSV_FILE}")
        return

    try:
        # 指定編碼以防 Windows 讀取中文亂碼
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')

        # --- 階段 1：趨勢篩選 ---
        df['slope'] = np.random.uniform(60, 80, len(df)) # 模擬斜率

        # --- 階段 2：避強擊弱核心邏輯 ---
        
        # 1. 競爭強度：排除商品數 >= 300 的強競品
        # (若 CSV 沒這欄位，此處模擬數據供你測試 UI)
        if '商品數' not in df.columns:
            df['商品數'] = np.random.randint(50, 500, len(df))
            
        df = df[df['商品數'] < 300].copy()

        # 2. 三維度 AI 評分模型
        # A. 競爭得分 (商品越少分越高)
        df['comp_score'] = 100 - (df['商品數'] / 3) 
        # B. 市場規模 (搜尋量越大分越高)
        df['scale_score'] = (df['搜尋量'] / df['搜尋量'].max()) * 100
        # C. 進入門檻 (綜合斜率與藍海值)
        df['barrier_score'] = df['slope'] * 1.2
        
        # 最終 Final_Score 權重分配
        df['Final_Score'] = (df['comp_score'] * 0.4) + (df['scale_score'] * 0.3) + (df['slope'] * 0.3)

        # 3. 輸出弱/中競品標籤 (符合 90+/70-90 邏輯)
        def get_comp_tag(row):
            if row['comp_score'] >= 90: return "弱競品(Low)-絕對進攻"
            if row['comp_score'] >= 70: return "中競品(Mid)-差異化競爭"
            return "觀察中"
        
        df['Competition_Tag'] = df.apply(get_comp_tag, axis=1)

        # 4. 去重複與排序
        df['prefix'] = df['關鍵字'].str[:3]
        df_final = df.sort_values('Final_Score', ascending=False).drop_duplicates('prefix')

        # 5. 存檔
        report = {
            "top_picks": df_final.head(30).to_dict(orient='records'),
            "all_others": df_final.iloc[30:].to_dict(orient='records'),
            "update_time": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
        }
        
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        
        print(f"✅ 分析完成！已過濾掉強競品（商品數 >= 300）")
        print(f"✅ 弱/中競品名單已產出至 {OUTPUT_JSON}")

    except Exception as e:
        print(f"❌ 發生錯誤：{e}")

@app.get("/api/report")
async def get_report():
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"error": "No data"}

if __name__ == "__main__":
    run_analysis_pipeline()
    # Windows CMD 執行建議使用 127.0.0.1
    uvicorn.run(app, host="127.0.0.1", port=8000)