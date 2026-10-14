# 資料視覺化專題｜問題 1–3

## 繳交與閱讀入口

| 成果 | 連結 | 用途 |
|---|---|---|
| **問題 1–3 合併 PDF** | [下載排版完成的 PDF](outputs/reports/submission/questions_1_2_3.pdf) | 22 頁，含三題報告、代表圖表與 AGENTS.md 附錄 |
| 合併 HTML | [下載離線 HTML](outputs/reports/submission/questions_1_2_3.html) | 圖片已內嵌，下載後以瀏覽器閱讀 |
| 問題 3 比較報告 | [六面向比較與限制](outputs/reports/question3/comparison_report.md) | 可直接在 GitHub 閱讀 |
| 問題 3 完整成果 | [question3_results.zip](downloads/question3_results.zip) | 兩次獨立測試的程式、原始輸入、圖表與驗證 |
| 全作業檔案 | [submission_bundle.zip](downloads/submission_bundle.zip) | 問題 1–3 的分類檔案與合併 PDF |

PDF 封面姓名、學號、組別請小組於繳交前補填。問題 4 的手寫 A4 不在本次 PDF 範圍內。GitHub 不會直接執行 HTML，互動圖需下載後用瀏覽器開啟。

## 題目與成果分類

| 題目 | 目標 | 報告與證據 |
|---|---|---|
| 問題 1 | 依 AGENTS.md 做實測 | [報告](outputs/reports/question1_test_report_v2.md)、[圖片](outputs/figures/) |
| 問題 2 | A 趨勢、B 關係、C 異常、D 互動 | [報告](outputs/reports/question2_run_04/question2_report.md)、[四任務圖片](outputs/figures/question2_run_04/) |
| 問題 3 | 相同資料與 Prompt，比較無／有規範 | [比較報告](outputs/reports/question3/comparison_report.md)、[實驗封存](experiments/question3/) |

```text
AGENTS.md                 共用規範，問題 3 未修改它
docs/                     題目原文／照片轉錄
data/raw/                 三份原始 CSV
data/processed/           問題 1、2 的處理與彙整資料
src/                      問題 1、2 分析程式及 PDF 建立程式
outputs/figures/          問題 1、2 圖片
outputs/html/             問題 2 互動 HTML
outputs/reports/          各題分析、驗證及 submission 合併報告
experiments/question3/    問題 3 兩次獨立 Agent 完整成果，保留原結構
downloads/                問題 2、3 及完整作業下載包
```

## 問題 3：兩次獨立測試

兩個全新 Agent 依序執行相同 Prompt：「請分析 data.csv 中的重要趨勢，並製作適合的資料視覺化。」第一次未提供小組規範，第二次提供原本 AGENTS.md；輸入 CSV 位元組相同，未修改資料。

| 項目 | 第一次：無規範 | 第二次：有規範 |
|---|---|---|
| 成果入口 | [完整目錄](experiments/question3/without_agents/) | [完整目錄](experiments/question3/with_agents/) |
| 分析報告 | [中文報告](experiments/question3/without_agents/outputs/analysis_report.md) | [中文報告](experiments/question3/with_agents/outputs/reports/analysis_v1.md) |
| 程式 | [analyze.py](experiments/question3/without_agents/analyze.py) | [src/analyze.py](experiments/question3/with_agents/src/analyze.py) |
| 圖片 | [四組 PNG/SVG](experiments/question3/without_agents/outputs/) | [三組 PNG](experiments/question3/with_agents/outputs/figures/) |
| 驗證 | [validation.json](experiments/question3/without_agents/outputs/validation.json) | [validation_v1.json](experiments/question3/with_agents/outputs/reports/validation_v1.json) |

兩次都主動檢查資料、實際執行並得到一致主要數值。有規範版本更符合指定分類、版本化保存與系列辨識。單次比較不能證明全面改善，也未量測 Prompt 節省比例；完整限制與方法差異均寫入比較報告。

- [相同 Prompt](outputs/reports/question3/test_prompt.txt)
- [實驗設計](outputs/reports/question3/experiment_design.json)
- [檔案 SHA-256 清單](outputs/reports/question3/artifact_manifest.json)
- [整理者獨立重算驗證](outputs/reports/question3/parent_validation.json)
- [兩次七張圖的視覺檢查](outputs/reports/question3/visual_review.md)

封存目錄是原始成果證據。若要重做無規範條件，應複製到不會繼承上層 AGENTS.md 的獨立工作目錄，並使用新的 Agent 對話；不能直接在此專案下重跑後稱為無規範實驗。

## 合併報告重建

`python3 src/build_submission.py` 需要 Playwright、系統 Chromium、pypdf 與 Noto Sans CJK 字型。程式為保護成果，若既有 PDF/HTML 已存在會停止；請先另存版本再重建。已在本雲端環境執行並檢視封面與問題 3 比較表版面，未宣稱在全新環境重建。

---

## 問題 1、2 詳細入口與執行說明

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
