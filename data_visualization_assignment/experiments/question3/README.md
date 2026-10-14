# 問題 3：獨立測試成果封存

| 條件 | 程式 | 報告 |
|---|---|---|
| 無小組規範 | [without_agents/analyze.py](without_agents/analyze.py) | [報告](without_agents/outputs/analysis_report.md) |
| 有小組規範 | [with_agents/src/analyze.py](with_agents/src/analyze.py) | [報告](with_agents/outputs/reports/analysis_v1.md) |

[六面向比較](../../outputs/reports/question3/comparison_report.md)｜[實驗設計與限制](../../outputs/reports/question3/experiment_design.json)

兩個目錄保留各 Agent 自行選擇的原始結構，避免整理時改寫實驗結果。輸入 data.csv 是相同原始資料的副本，雜湊一致。

原始實驗在 /workspace/question3_experiment 下兩個獨立目錄執行。此處為 GitHub 證據封存；重跑可能繼承專案根目錄的 AGENTS.md，不能當成新的無規範實驗。
