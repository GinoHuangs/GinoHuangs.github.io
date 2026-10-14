# 演算法測量資料分析

分析 `data.csv` 的輸入規模趨勢，將搜尋與排序分開比較。原始檔未修改。

## 閱讀成果

- [完整中文報告（Markdown）](outputs/reports/analysis_v1.md)
- [可離線開啟的完整報告（HTML，內嵌三張圖）](outputs/reports/analysis_v1.html)
- [耗時趨勢圖](outputs/figures/runtime_trends_v1.png)
- [記憶體趨勢與極端值](outputs/figures/memory_trends_v1.png)
- [比較次數趨勢圖](outputs/figures/comparison_trends_v1.png)
- [資料品質檢查](outputs/reports/data_quality_v1.json)
- [程式驗證結果](outputs/reports/validation_v1.json)
- [實際圖片視覺檢查與檔案驗證](outputs/reports/visual_review_v1.json)
- [逐筆處理後資料與品質旗標](data/processed/observations_v1.csv)
- [28 組統計摘要](data/processed/group_summary_v1.csv)

## 環境與執行

本次已在 Python 3.12.14、pandas 2.2.3、NumPy 2.3.5、Matplotlib 3.10.8 與現有 Pillow 環境實際執行。未新增或升級套件。Pillow 用於圖片解碼驗證。

在此專案目錄執行：

```bash
MPLCONFIGDIR=/tmp/q3_with_agents_mpl XDG_CACHE_HOME=/tmp/q3_with_agents_cache python src/analyze.py
```

不需圖形桌面、不需網路。快取寫入 `/tmp`，不寫入唯讀使用者家目錄。程式相對於自身位置讀取專案 `data.csv`，新增 `data/processed/`、`outputs/figures/` 及 `outputs/reports/` 內的成果。再次執行時產生 v2、v3 等新版本，不覆寫既有結果。

## 主要結果

- 224 筆、4 種演算法、7 種規模，每組 8 次重複。1 筆缺失耗時、1 筆零耗時、1 筆負比較次數只從該指標分析排除；420 MB 極端值標記並保留。18 筆 0.05 ms 保留且註明可能的計時下限。
- n=1,000 時 Linear Search 中位耗時較低；n=5,000 時 Binary Search 較低。n=100,000 時為 179.6865 與 7.0290 ms。
- n=100,000 時 Quick Sort 相較 Merge Sort，中位耗時低 21.1%、記憶體低 34.3%。
- 圖表以中位數與第 25–75 百分位數呈現重複測量，原始點保留於耗時、比較次數與記憶體完整視圖；圖表英文標籤避免中文字型問題。

## 已驗證與限制

實際執行成功，28 組摘要的計數與中位數重新計算一致；三張 180 dpi PNG 均可解碼，並已檢視標籤、圖例與版面；原檔 SHA-256 不變。另確認 HTML 內嵌三張圖，無外部圖片依賴。

每組樣本少，且缺少硬體、實作、計時方式及輸入分布等背景。無日期欄，這是輸入規模趨勢而非時間趨勢。未做因果推論、統計顯著性宣稱或跨任務效能排名；極端值與計時下限仍待資料來源確認。沒有互動圖表；HTML 僅作離線靜態展示，未做瀏覽器操作測試。
