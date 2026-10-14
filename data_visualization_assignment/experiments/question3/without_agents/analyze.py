#!/usr/bin/env python3
"""Reproducible analysis of data.csv; input is never modified."""
from pathlib import Path
import base64
import hashlib
import html
import json
import os
import platform

os.environ.setdefault("MPLCONFIGDIR", "/tmp/question3-without-agents-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/question3-without-agents-cache")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
SOURCE = ROOT / "data.csv"
original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
raw = pd.read_csv(SOURCE, encoding="utf-8-sig")
required = {"run_id", "algorithm", "input_size", "repeat", "runtime_ms", "memory_mb", "comparisons"}
if set(raw.columns) != required:
    raise ValueError(f"Unexpected columns: {list(raw.columns)}")
if raw.run_id.duplicated().any() or raw.duplicated(["algorithm", "input_size", "repeat"]).any():
    raise ValueError("Duplicate experiment identifiers require review")
if raw[list(required - {"run_id", "algorithm", "runtime_ms"})].isna().any().any():
    raise ValueError("Unexpected missing values")
if (raw.input_size <= 0).any():
    raise ValueError("Input size must be positive")

algorithms = ["Linear_Search", "Binary_Search", "Merge_Sort", "Quick_Sort"]
labels = {"Linear_Search": "線性搜尋", "Binary_Search": "二分搜尋", "Merge_Sort": "合併排序", "Quick_Sort": "快速排序"}
colors = dict(zip(algorithms, ["#D55E00", "#0072B2", "#009E73", "#CC79A7"]))
data = raw.copy()
issues = []
for metric in ["runtime_ms", "memory_mb", "comparisons"]:
    for idx in raw.index[raw[metric].isna()]:
        issues.append({"run_id": raw.at[idx, "run_id"], "metric": metric, "value": None,
                       "issue": "missing", "action": "Exclude this metric only; no imputation"})
    invalid = raw[metric].le(0) if metric != "comparisons" else raw[metric].lt(0)
    for idx in raw.index[invalid]:
        issues.append({"run_id": raw.at[idx, "run_id"], "metric": metric, "value": float(raw.at[idx, metric]),
                       "issue": "invalid nonpositive measurement" if metric != "comparisons" else "negative count",
                       "action": "Exclude this metric only; retain other measurements"})
    data.loc[invalid, metric] = np.nan

# A groupwise Tukey rule only flags potential anomalies; it never deletes data.
q1 = raw.groupby(["algorithm", "input_size"])["memory_mb"].transform(lambda x: x.quantile(.25))
q3 = raw.groupby(["algorithm", "input_size"])["memory_mb"].transform(lambda x: x.quantile(.75))
memory_flags = (raw.memory_mb < q1 - 1.5 * (q3 - q1)) | (raw.memory_mb > q3 + 1.5 * (q3 - q1))
for idx in raw.index[memory_flags]:
    issues.append({"run_id": raw.at[idx, "run_id"], "metric": "memory_mb", "value": float(raw.at[idx, "memory_mb"]),
                   "issue": "outside within-group 1.5 IQR fences", "action": "Retain; use median and IQR; inspect separately"})
pd.DataFrame(issues).to_csv(OUT / "quality_issues.csv", index=False)
data.to_csv(OUT / "analysis_data.csv", index=False)

records = []
for (algorithm, size), group in data.groupby(["algorithm", "input_size"]):
    for metric in ["runtime_ms", "memory_mb", "comparisons"]:
        values = group[metric].dropna()
        records.append(dict(algorithm=algorithm, input_size=int(size), metric=metric,
                            n_total=len(group), n_valid=len(values), median=values.median(),
                            q25=values.quantile(.25), q75=values.quantile(.75),
                            mean=values.mean(), std=values.std(), minimum=values.min(), maximum=values.max()))
summary = pd.DataFrame(records)
summary.to_csv(OUT / "summary.csv", index=False)
indexed = summary.set_index(["algorithm", "input_size", "metric"])

def value(algorithm, size, metric="runtime_ms"):
    return float(indexed.loc[(algorithm, size, metric), "median"])

available_fonts = {f.name for f in font_manager.fontManager.ttflist}
font = "Noto Sans CJK JP" if "Noto Sans CJK JP" in available_fonts else "DejaVu Sans"
plt.rcParams.update({"font.family": font, "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.unicode_minus": False,
                     "figure.facecolor": "white", "axes.titleweight": "bold", "svg.fonttype": "path"})
figures = []

def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=180, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    figures.append(name)

def trend(ax, metric, algs, raw_points=False):
    for alg in algs:
        subset = summary[(summary.algorithm == alg) & (summary.metric == metric)].sort_values("input_size")
        xs = subset.input_size.to_numpy()
        ax.plot(xs, subset["median"], color=colors[alg], marker="o", lw=2, label=labels[alg], zorder=3)
        ax.fill_between(xs, subset.q25.to_numpy(), subset.q75.to_numpy(), color=colors[alg], alpha=.17)
        if raw_points:
            points = data[data.algorithm == alg].dropna(subset=[metric])
            # Deterministic horizontal displacement shows repeated measurements.
            ax.scatter(points.input_size * np.exp((points.repeat - 4.5) * .012), points[metric],
                       color=colors[alg], s=15, alpha=.4, edgecolors="none", zorder=2)
    ax.set_xscale("log")
    ax.set_xlabel("輸入規模 n（對數刻度）")
    ax.grid(alpha=.22, which="major")
    ax.legend(frameon=False)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))

fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
for ax, algs, title in zip(axes, [algorithms[:2], algorithms[2:]], ["搜尋：優勢隨規模反轉", "排序：快速排序在較大規模持續較快"]):
    trend(ax, "runtime_ms", algs, raw_points=True)
    ax.set_yscale("log")
    ax.set_ylabel("耗時（ms，對數刻度）")
    ax.set_title(title)
axes[0].annotate("n = 100,000：二分搜尋快 25.6 倍", xy=(100000, value("Binary_Search", 100000)),
                 xytext=(1400, .14), arrowprops={"arrowstyle": "->", "color": "#555"}, fontsize=10)
fig.suptitle("耗時隨輸入規模的變化", fontsize=18, y=1.03)
fig.text(.5, -.035, "線：有效量測中位數｜色帶：第 25–75 百分位｜點：個別量測（僅水平錯開）\n缺漏及零耗時不計入；0.05 ms 保留。搜尋與排序完成的任務不同。", ha="center", fontsize=10)
fig.tight_layout()
save(fig, "01_runtime")

fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
trend(axes[0], "comparisons", algorithms)
axes[0].set_yscale("log")
axes[0].set_ylabel("比較次數（對數刻度）")
axes[0].set_title("比較次數：二分搜尋成長最慢")
normalization = []
for alg in algorithms:
    subset = summary[(summary.algorithm == alg) & (summary.metric == "comparisons") & (summary.input_size >= 1000)].copy()
    n = subset.input_size.to_numpy()
    scale = n if alg == "Linear_Search" else np.log2(n) if alg == "Binary_Search" else n * np.log2(n)
    ratio = subset["median"].to_numpy() / scale
    axes[1].plot(n, ratio, marker="o", color=colors[alg], label=labels[alg])
    for size, r in zip(n, ratio):
        normalization.append({"algorithm": alg, "input_size": int(size), "comparisons_divided_by_expected_scale": float(r)})
axes[1].set_xscale("log")
axes[1].set_ylim(.5, 1.1)
axes[1].set_xlabel("輸入規模 n（對數刻度）")
axes[1].set_ylabel("比較次數中位數 ÷ 對應成長函數")
axes[1].set_title("標準化後大致穩定（n ≥ 1,000）")
axes[1].grid(alpha=.22)
axes[1].legend(frameon=False)
fig.suptitle("操作量與演算法的成長型態", fontsize=18, y=1.03)
fig.text(.5, -.035, "線性搜尋除以 n；二分搜尋除以 log2(n)；兩種排序除以 n log2(n)。\n曲線接近平坦支持相應成長型態，但有限規模的量測不能證明漸近複雜度；負比較次數按缺值處理。", ha="center", fontsize=10)
fig.tight_layout()
save(fig, "02_comparisons")
pd.DataFrame(normalization).to_csv(OUT / "normalized_comparisons.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={"width_ratios": [1.5, 1]})
trend(axes[0], "memory_mb", algorithms)
axes[0].set_ylim(15, 47)
axes[0].set_ylabel("記憶體（MB）")
axes[0].set_title("典型記憶體用量：排序隨規模增加")
axes[0].text(.02, .96, "此面板顯示中位數與 IQR；420 MB 單點見右圖", transform=axes[0].transAxes, va="top", fontsize=9)
spike_group = raw[(raw.algorithm == "Binary_Search") & (raw.input_size == 10000)]
axes[1].scatter(spike_group.repeat, spike_group.memory_mb, color=colors["Binary_Search"], s=55)
axes[1].axhline(spike_group.memory_mb.median(), color="#222", label=f"中位數 {spike_group.memory_mb.median():.2f} MB")
axes[1].axhline(spike_group.memory_mb.mean(), color="#D55E00", linestyle="--", label=f"平均數 {spike_group.memory_mb.mean():.2f} MB")
axes[1].annotate("RUN0090：420 MB\n保留於主分析", xy=(2, 420), xytext=(3.2, 335), arrowprops={"arrowstyle": "->"}, fontsize=10)
axes[1].set(title="異常量測會明顯拉高平均數", xlabel="重複量測編號", ylabel="記憶體（MB）", ylim=(0, 460), xticks=range(1, 9))
axes[1].grid(alpha=.22)
axes[1].legend(frameon=False)
fig.suptitle("記憶體趨勢與異常值敏感度", fontsize=18, y=1.03)
fig.text(.5, -.015, "色帶為第 25–75 百分位，並非信賴區間。異常旗標僅供檢視，不直接刪除記憶體量測。", ha="center", fontsize=10)
fig.tight_layout()
save(fig, "03_memory")

fig, ax = plt.subplots(figsize=(10, 5))
scaling_records = []
for alg in algorithms:
    subset = summary[(summary.algorithm == alg) & (summary.metric == "runtime_ms") & (summary.input_size >= 1000)]
    n = subset.input_size.to_numpy()
    scale = n if alg == "Linear_Search" else np.log2(n) if alg == "Binary_Search" else n * np.log2(n)
    normalized = subset["median"].to_numpy() / scale
    ratios = normalized / normalized[0]
    ax.plot(n, ratios, marker="o", lw=2, color=colors[alg], label=labels[alg])
    for size, norm, ratio in zip(n, normalized, ratios):
        scaling_records.append(dict(algorithm=alg, input_size=int(size), normalized_runtime=float(norm), relative_to_n1000=float(ratio)))
ax.axhline(1, color="#666", ls="--", lw=1)
ax.set_xscale("log")
ax.set(xlabel="輸入規模 n（對數刻度）", ylabel="耗時 ÷ 成長函數，再以 n=1,000 為 1", ylim=(.8, 1.4), title="規模增加後，標準化耗時大致穩定")
ax.grid(alpha=.2)
ax.legend(frameon=False, ncol=2)
fig.text(.5, -.015, "成長函數：線性搜尋 n；二分搜尋 log2(n)；排序 n log2(n)。各線各自定基，不比較跨演算法的絕對速度。", ha="center", fontsize=10)
fig.tight_layout()
save(fig, "04_runtime_scaling")
pd.DataFrame(scaling_records).to_csv(OUT / "runtime_scaling.csv", index=False)

floor_counts = raw[raw.runtime_ms.eq(.05)].groupby(["algorithm", "input_size"]).size()
floor_counts.rename("runtime_equals_0_05_count").to_csv(OUT / "runtime_floor_counts.csv")
quick_saving = 100 * (1 - value("Quick_Sort", 100000) / value("Merge_Sort", 100000))
memory_saving = 100 * (1 - value("Quick_Sort", 100000, "memory_mb") / value("Merge_Sort", 100000, "memory_mb"))
search_speedup = value("Linear_Search", 100000) / value("Binary_Search", 100000)
summary_rows = []
for n in sorted(data.input_size.unique()):
    summary_rows.append("| " + f"{n:,}" + " | " + " | ".join(f"{value(a,n):.4f}" for a in algorithms) + " |")
growth_rows = []
for a in algorithms:
    growth_rows.append(f"| {labels[a]} | {value(a,1000):.4f} | {value(a,100000):.4f} | {value(a,100000)/value(a,1000):.2f} 倍 |")
issue_rows = []
for issue in issues:
    issue_rows.append(f"| {issue['run_id']} | {issue['metric']} | {issue['value']} | {issue['issue']} | {issue['action']} |")
report = f"""# 演算法效能資料分析

## 主要發現

1. **搜尋效能出現規模轉折。** 在已測的 n=100、500、1,000，線性搜尋的中位耗時較低；從 n=5,000 起，二分搜尋較快。n=100,000 時，線性搜尋為 {value('Linear_Search',100000):.4f} ms，二分搜尋為 {value('Binary_Search',100000):.4f} ms，後者快 **{search_speedup:.2f} 倍**。只能確定已測點的優勢在 1,000 與 5,000 之間反轉，沒有量到精確交叉點。
2. **較大輸入下，快速排序兼具較低耗時與記憶體。** n≥1,000 的各組中位耗時均低於合併排序；n=100,000 時為 {value('Quick_Sort',100000):.4f} vs. {value('Merge_Sort',100000):.4f} ms，快速排序耗時低 **{quick_saving:.1f}%**。記憶體中位數為 {value('Quick_Sort',100000,'memory_mb'):.3f} vs. {value('Merge_Sort',100000,'memory_mb'):.3f} MB，低 **{memory_saving:.1f}%**。
3. **操作次數呈現不同成長型態。** n=100,000 時，二分搜尋比較次數中位數僅 16，線性搜尋為 67,616，兩種排序約 144 萬。n≥1,000 時，將比較次數分別除以 log2(n)、n 或 n log2(n) 後大致穩定，支持相應的成長趨勢。不同任務的操作數不能直接作為演算法優劣排名。
4. **記憶體的一次尖峰會誤導平均數。** 二分搜尋 n=10,000 的 RUN0090 為 420 MB，其餘七次介於 17.56–19.03 MB。該組平均數為 {spike_group.memory_mb.mean():.2f} MB，中位數僅 {spike_group.memory_mb.median():.2f} MB；尖峰保留在分析中並獨立呈現。

## 資料與處理原則

- 原始資料 **224 筆、7 欄**；4 種演算法 × 7 種輸入規模（100 至 100,000）× 每組 8 次。沒有重複 run_id 或重複的演算法／規模／重複編號組合。
- 這是**輸入規模趨勢**，資料沒有時間欄位；run_id 與 repeat 不當成時間序列。
- RUN0024 缺少 runtime_ms；RUN0142 runtime_ms=0 視為無效耗時；RUN0193 comparisons=-10 視為無效比較次數。只排除該欄位，不刪整列，也不補值。因此有效耗時 **222 筆**、記憶體 **224 筆**、比較次數 **223 筆**。
- 記憶體使用各演算法／規模組內 1.5 IQR 規則標記潛在離群值，**不刪除**；完整清單見 quality_issues.csv。旗標不代表量測必然錯誤，也不以此推論成因。
- 有 **18 筆耗時等於 0.05 ms**（17 筆在 n≤500，另 1 筆在 n=1,000）。可能與量測解析度、下限截斷或資料生成方式有關，資料不足以判定。保留這些值，但不把小規模的細微排序視為穩健結論。
- 分組以**中位數與第 25–75 百分位（IQR）**為主；色帶表示量測分散程度，**不是信賴區間**。缺值排除後有 7 筆的組別會按 7 筆計算；其餘為 8 筆。

## 耗時趨勢

![耗時趨勢](01_runtime.png)

各規模的耗時中位數（ms；按有效量測計算）：

| 輸入規模 | 線性搜尋 | 二分搜尋 | 合併排序 | 快速排序 |
|---:|---:|---:|---:|---:|
{chr(10).join(summary_rows)}

輸入從 1,000 增加至 100,000（100 倍）時：

| 演算法 | n=1,000 耗時（ms） | n=100,000 耗時（ms） | 耗時成長 |
|---|---:|---:|---:|
{chr(10).join(growth_rows)}

![標準化耗時](04_runtime_scaling.png)

標準化耗時在較大規模下大致平穩。這是有限量測範圍的描述，不是對程式實作或理論複雜度的證明；線性搜尋 n=1,000 的基準組也有一筆缺失，需一併考量。

## 比較次數

![比較次數](02_comparisons.png)

二分搜尋在輸入增加時的比較次數增長很小，解釋了它在大型輸入的速度優勢。兩種排序在 n=100,000 的比較次數相近，但耗時仍有差異；僅憑這份資料無法把耗時差異歸因於比較次數、常數成本、記憶體存取或實作細節中的某一項。

## 記憶體

![記憶體趨勢與異常](03_memory.png)

二分搜尋各規模的記憶體中位數介於 17.665–18.570 MB，線性搜尋在 n=100,000 時為 20.540 MB；排序的記憶體在大規模時增加較明顯。記憶體欄位未說明是峰值、平均值或額外配置量，故不將其解釋為理論輔助空間。

## 解讀限制與建議

- 搜尋與排序解決不同問題，應在同類演算法間比較。二分搜尋通常需要已排序輸入；資料未說明是否計入排序前處理，不能直接推導任意搜尋工作流程的總成本。
- 沒有硬體、語言、實作、資料分布、搜尋命中位置、計時方式、隨機種子或實驗順序資料。相同 repeat 編號不代表配對樣本；此分析不採用配對推論。
- 每組僅 8 次，未做統計顯著性或泛化性能宣稱。排序在小規模的差距尤其容易受量測下限和變動影響。
- 若目標是大量已排序資料的搜尋，優先評估二分搜尋；若目標是本實驗條件下的大規模排序，快速排序表現較好。正式採用前應補測 1,000–5,000 的搜尋轉折、調查 420 MB 尖峰，並改善小規模計時方式與增加重複次數。

## 重現與輸出

在此目錄執行：`python analyze.py`。僅需已安裝的 Python、pandas、NumPy 與 Matplotlib；不需下載套件或連網。程式自動將快取放到 /tmp，並使用可用的 Noto Sans CJK JP 字型。

- `analysis_report.html`：可離線開啟，圖像已嵌入。
- `analysis_report.md`：本報告；四張圖皆有 PNG 與 SVG。
- `summary.csv`：84 組「演算法 × 規模 × 指標」的有效筆數、中位數、IQR、平均數、標準差與極值。
- `analysis_data.csv`：逐欄處理後的分析資料；原始 data.csv 不變。
- `quality_issues.csv`、`runtime_floor_counts.csv`：資料品質與 0.05 ms 集中情況。
- `normalized_comparisons.csv`、`runtime_scaling.csv`：標準化趨勢數值。
- `validation.json`：版本、輸入 SHA-256、資料筆數、輸出與執行驗證結果。
"""
(OUT / "analysis_report.md").write_text(report, encoding="utf-8")

# Minimal Markdown renderer for this report; all image assets are embedded.
def render_markdown(text):
    import re
    lines = text.splitlines()
    rendered = []
    in_list = False
    table = []
    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", s)
        return re.sub(r"`(.*?)`", r"<code>\1</code>", s)
    def flush_table():
        if not table:
            return
        rendered.append('<div class="table-wrap"><table>')
        for i, row in enumerate(table):
            if i == 1:
                continue
            tag = "th" if i == 0 else "td"
            rendered.append("<tr>" + "".join(f"<{tag}>{inline(c.strip())}</{tag}>" for c in row.strip("|").split("|")) + "</tr>")
        rendered.append("</table></div>")
        table.clear()
    for line in lines:
        if line.startswith("|"):
            table.append(line)
            continue
        flush_table()
        is_list = line.startswith("- ") or bool(re.match(r"\d+\. ", line))
        if in_list and not is_list:
            rendered.append("</ul>")
            in_list = False
        if not line:
            continue
        image_match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
        if image_match:
            encoded = base64.b64encode((OUT / image_match[2]).read_bytes()).decode("ascii")
            rendered.append(f'<figure><img alt="{html.escape(image_match[1])}" src="data:image/png;base64,{encoded}"></figure>')
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            rendered.append(f"<h{level}>{inline(line[level:].strip())}</h{level}>")
        elif is_list:
            if not in_list:
                rendered.append("<ul>")
                in_list = True
            rendered.append("<li>" + inline(re.sub(r"^(?:- |\d+\. )", "", line)) + "</li>")
        else:
            rendered.append("<p>" + inline(line) + "</p>")
    flush_table()
    if in_list:
        rendered.append("</ul>")
    return "\n".join(rendered)

document = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>演算法效能分析</title><style>body{font-family:system-ui,"Noto Sans CJK JP",sans-serif;max-width:1100px;margin:auto;padding:32px;color:#1d2939;line-height:1.8;background:#fff}h1{font-size:32px}h2{margin-top:42px;border-bottom:2px solid #e4e7ec}li{margin:10px 0}img{width:100%;height:auto}figure{margin:20px 0}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:8px 12px;border-bottom:1px solid #ddd;text-align:right}th{background:#f2f4f7}code{background:#f2f4f7;padding:2px 5px;border-radius:4px}@media print{body{padding:0}figure{break-inside:avoid}}</style><body>'''
(OUT / "analysis_report.html").write_text(document + render_markdown(report) + "</body></html>", encoding="utf-8")

# Validate actual artifacts and internal consistency after the analysis ran.
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == original_hash, "Input changed"
assert len(raw) == 224 and raw.algorithm.nunique() == 4 and raw.input_size.nunique() == 7
assert raw.groupby(["algorithm", "input_size"]).size().eq(8).all()
assert data.runtime_ms.notna().sum() == 222
assert data.memory_mb.notna().sum() == 224
assert data.comparisons.notna().sum() == 223
assert len(summary) == 84 and summary.n_valid.between(7, 8).all()
assert data.loc[data.run_id == "RUN0090", "memory_mb"].iat[0] == 420
assert len(issues) >= 4
assert raw.runtime_ms.eq(.05).sum() == 18
for name in figures:
    assert (OUT / f"{name}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "<svg" in (OUT / f"{name}.svg").read_text()
assert (OUT / "analysis_report.html").read_text().count('src="data:image/png;base64,') == 4
validation = dict(status="passed", input_sha256=original_hash, input_unchanged=True,
                  raw_rows=len(raw), groups=28, summary_rows=len(summary),
                  valid_counts={m: int(data[m].notna().sum()) for m in ["runtime_ms", "memory_mb", "comparisons"]},
                  issue_count=len(issues), memory_flag_run_ids=raw.loc[memory_flags, "run_id"].tolist(),
                  runtime_floor_count=18, charts_verified=figures, embedded_html_images=4, font=font,
                  versions={"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "matplotlib": matplotlib.__version__},
                  files=sorted(p.name for p in OUT.iterdir() if p.is_file() and p.name != "validation.json"))
(OUT / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(validation, ensure_ascii=False, indent=2))
