# data.csv 效能分析

執行方式：

```bash
cd /workspace/question3_experiment/without_agents
python analyze.py
```

依賴既有 Python、pandas、NumPy、Matplotlib；不需網路。程式自動將快取設於 `/tmp`，不修改 `data.csv`。

先開啟 [離線完整報告](outputs/analysis_report.html)，或閱讀 [Markdown 報告](outputs/analysis_report.md)。四張視覺化保存在 `outputs/01_runtime.*`、`02_comparisons.*`、`03_memory.*`、`04_runtime_scaling.*`，皆有 PNG 與 SVG。

摘要統計為 `outputs/summary.csv`；逐欄處理後資料為 `outputs/analysis_data.csv`；資料品質紀錄為 `outputs/quality_issues.csv`；實際驗證結果與輸入 SHA-256 為 `outputs/validation.json`。

耗時與比較次數中的無效值只排除該欄位。記憶體離群旗標不刪除資料；圖表用中位數與 IQR，完整報告說明樣本數、量測下限、任務可比性與實驗資訊缺失等限制。
