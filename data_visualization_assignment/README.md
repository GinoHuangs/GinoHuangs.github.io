# 資料視覺化作業：成果索引

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


## 檔案分類

| 分類 | 位置 | 內容 |
|---|---|---|
| 共用規範 | [AGENTS.md](AGENTS.md) | 問題 1、2 使用同一份規範 |
| 作業題目 | [docs/](docs/) | 問題 2 題目原文 |
| 原始資料 | [data/raw/](data/raw/) | 三份原始 CSV，共用、不重複上傳 |
| 分析資料 | [data/processed/](data/processed/) | 問題 1 彙整表與問題 2 四任務分析資料 |
| Python 程式 | [src/](src/) | 問題 1 test_question1.py、問題 2 question2_tasks.py |
| 圖片 | [outputs/figures/](outputs/figures/) | 問題 1 圖片與問題 2 A～D 圖片 |
| 互動網頁 | [outputs/html/](outputs/html/) | 問題 2 D 的獨立 HTML |
| 分析及驗證報告 | [outputs/reports/](outputs/reports/) | 資料檢查、分析說明與互動功能驗證 |
| 下載包 | [downloads/](downloads/) | 問題 2 完整 ZIP；問題 1 ZIP 保留於原位置 |

## 問題 2：A → B → C → D

問題 2 正式成果位於各分類中的 `question2_run_04/`。04 是完成驗證的執行批次編號，不是問題 4；未上傳先前失敗批次、暫存依賴或遮住圖例的初版截圖。

| 任務 | 圖片 | 相關成果 |
|---|---|---|
| A 效能趨勢 | [折線與誤差棒](outputs/figures/question2_run_04/a_performance_trend.png) | [時間彙整 CSV](data/processed/question2_run_04/a_runtime_summary.csv) |
| B 變數關係 | [散佈圖與箱型圖](outputs/figures/question2_run_04/b_variable_relationship.png) | 複雜度與缺陷數 Spearman ρ = 0.141，不能推論因果 |
| C 異常探索 | [分組 IQR 圖](outputs/figures/question2_run_04/c_latency_outliers.png) | [83 筆候選](data/processed/question2_run_04/c_latency_outliers.csv)、[端點門檻](data/processed/question2_run_04/c_iqr_thresholds.csv) |
| D 互動探索 | [互動圖截圖](outputs/figures/question2_run_04/d_interactive_explorer_clean.png) | [互動 HTML](outputs/html/question2_run_04/d_web_service_explorer.html) |

- [完整分析報告](outputs/reports/question2_run_04/question2_report.md)
- [互動功能測試結果](outputs/reports/question2_run_04/interactive_validation.json)
- [圖片檢查紀錄](outputs/reports/question2_run_04/visual_review.md)
- [資料品質檢查](outputs/reports/question2_run_04/data_quality.json)
- [問題 2 完整下載包](downloads/question2_results.zip)

### 互動圖使用方式

GitHub 的檔案檢視頁不會直接執行互動 HTML。下載 HTML（或完整 ZIP 解壓縮）後，用瀏覽器開啟；JavaScript 已內嵌，不需另外連線下載 Plotly。

### 問題 2 執行方式

在此作業資料夾安裝 Plotly 至專用目錄：

```bash
python3 -m pip install --target .deps plotly==6.3.1
python3 src/question2_tasks.py
```

另需 pandas、Matplotlib、Seaborn、Pillow、Playwright、系統 Chromium（程式使用 /usr/bin/chromium）及 Noto Sans CJK 字型。程式會新增 run 資料夾，避免覆寫。已驗證的是本雲端環境；未在全新環境重建測試。
