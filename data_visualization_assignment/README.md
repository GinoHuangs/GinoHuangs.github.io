# 問題 1：資料視覺化實測

從本資料夾執行：

```bash
python3 src/test_question1.py
```

使用 Python、pandas、Matplotlib、Seaborn、Pillow；中文字型為 Noto Sans CJK TC。
原始 CSV 在 data/raw/，圖片在 outputs/figures/，測試報告在 outputs/reports/。
重跑時輸出以版本號另存，不覆寫既有成果。

## 問題 1 成果

- [演算法效能圖](outputs/figures/algorithm_runtime_v2.png)
- [軟體品質分析圖](outputs/figures/software_quality_v2.png)
- [網站服務分析圖](outputs/figures/web_service_v2.png)
- [測試報告](outputs/reports/question1_test_report_v2.md)
- [資料品質檢查](outputs/reports/data_quality_v2.json)
- [圖片檢查紀錄](outputs/reports/visual_review.md)
- [完整下載包](question1_results.zip)

本次測試為同一 Agent 依規範執行的分析，不是獨立 Agent 盲測。
因交付目標為靜態圖片，使用 Matplotlib 與 Seaborn，未產出 Plotly 互動圖。
程式顯式載入系統 Noto Sans CJK 字型；其他機器若缺少字型，需先配置可用中文字型。
已驗證套件版本：pandas 2.2.3、Matplotlib 3.10.8、Seaborn 0.13.2。
原始資料含 1 筆執行時間缺失與 1 筆負比較次數，處理方式詳見報告。
