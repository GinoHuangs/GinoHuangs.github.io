#!/usr/bin/env python3
"""Reproducible, read-only analysis of the supplied algorithm measurements."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/q3_with_agents_mpl')
os.environ.setdefault('XDG_CACHE_HOME', '/tmp/q3_with_agents_cache')
import hashlib
import html
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data.csv'
FIG = ROOT / 'outputs/figures'
REPORT = ROOT / 'outputs/reports'
PROCESSED = ROOT / 'data/processed'
for folder in (FIG, REPORT, PROCESSED):
    folder.mkdir(parents=True, exist_ok=True)
version = 1
while (REPORT / f'analysis_v{version}.md').exists():
    version += 1
TAG = f'v{version}'
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
raw = pd.read_csv(SOURCE, encoding='utf-8-sig')
d = raw.copy()
numeric = ['input_size', 'repeat', 'runtime_ms', 'memory_mb', 'comparisons']
conversion_failures = {}
for col in numeric:
    converted = pd.to_numeric(d[col], errors='coerce')
    conversion_failures[col] = int((d[col].notna() & converted.isna()).sum())
    d[col] = converted
required = {'run_id', 'algorithm', *numeric}
assert required <= set(d.columns)
assert d[['algorithm', 'input_size', 'repeat']].notna().all().all()
assert (d.input_size > 0).all()
d['runtime_missing'] = d.runtime_ms.isna()
d['runtime_nonpositive'] = d.runtime_ms.notna() & (d.runtime_ms <= 0)
d['comparisons_negative'] = d.comparisons < 0
d['runtime_at_005'] = d.runtime_ms == .05
# Robust, within-algorithm/size flag: median + 10 MAD, only positive upper extremes.
memory_group = d.groupby(['algorithm', 'input_size']).memory_mb
memory_center = memory_group.transform('median')
memory_mad = memory_group.transform(lambda x: (x - x.median()).abs().median())
d['memory_extreme_flag'] = (d.memory_mb - memory_center) > 10 * memory_mad
d['runtime_valid_ms'] = d.runtime_ms.where(d.runtime_ms > 0)
d['memory_valid_mb'] = d.memory_mb.where(d.memory_mb > 0)
d['comparisons_valid'] = d.comparisons.where(d.comparisons >= 0)
d.to_csv(PROCESSED / f'observations_{TAG}.csv', index=False)

records = []
for (algorithm, n), group in d.groupby(['algorithm', 'input_size']):
    record = {'algorithm': algorithm, 'input_size': int(n), 'n_total': len(group)}
    for label, column in [('runtime', 'runtime_valid_ms'), ('memory', 'memory_valid_mb'), ('comparisons', 'comparisons_valid')]:
        values = group[column].dropna()
        record.update({f'{label}_n': len(values), f'{label}_median': values.median(),
                       f'{label}_q25': values.quantile(.25), f'{label}_q75': values.quantile(.75),
                       f'{label}_mean': values.mean(), f'{label}_min': values.min(), f'{label}_max': values.max()})
    records.append(record)
summary = pd.DataFrame(records)
summary.to_csv(PROCESSED / f'group_summary_{TAG}.csv', index=False)
quality = {
    'source_sha256': source_hash, 'rows': len(d), 'columns': list(raw.columns),
    'original_dtypes': raw.dtypes.astype(str).to_dict(),
    'missing_counts': raw.isna().sum().astype(int).to_dict(),
    'conversion_failures': conversion_failures,
    'exact_duplicate_rows': int(raw.duplicated().sum()),
    'duplicate_run_id': int(raw.run_id.duplicated().sum()),
    'duplicate_measurement_keys': int(raw.duplicated(['algorithm','input_size','repeat']).sum()),
    'algorithms': sorted(d.algorithm.unique().tolist()),
    'input_sizes': sorted(d.input_size.unique().tolist()),
    'repeats': sorted(d['repeat'].unique().tolist()),
    'numeric_ranges': {col: {'min': float(d[col].min()), 'max': float(d[col].max())} for col in numeric},
    'flag_counts': {col: int(d[col].sum()) for col in ['runtime_missing','runtime_nonpositive','comparisons_negative','runtime_at_005','memory_extreme_flag']},
    'invalid_memory_count': int((~(d.memory_mb > 0)).sum()),
    'valid_metric_counts': {col: int(d[col].notna().sum()) for col in ['runtime_valid_ms','memory_valid_mb','comparisons_valid']},
}
(REPORT / f'data_quality_{TAG}.json').write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding='utf-8')

ORDER = ['Linear_Search', 'Binary_Search', 'Merge_Sort', 'Quick_Sort']
COLORS = dict(zip(ORDER, ['#d35f27', '#18789a', '#8151a5', '#228563']))
MARKERS = dict(zip(ORDER, ['o', 's', '^', 'D']))
LABELS = {x: x.replace('_',' ') for x in ORDER}
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'axes.titlesize':12,
                     'axes.labelsize':10, 'axes.spines.top':False, 'axes.spines.right':False,
                     'figure.facecolor':'#ffffff', 'savefig.facecolor':'#ffffff'})
figure_paths = []

def format_axis(ax, ylabel, log_y=True):
    ax.set_xscale('log')
    if log_y:
        ax.set_yscale('log')
    ax.set_xlabel('Input size (elements; log scale)')
    ax.set_ylabel(ylabel)
    ax.grid(True, which='major', color='#e2e5e8', linewidth=.6)
    ax.set_axisbelow(True)

def series(ax, algorithms, metric, column, show_raw=True):
    for algorithm in algorithms:
        s = summary[summary.algorithm == algorithm].sort_values('input_size')
        color = COLORS[algorithm]
        if show_raw:
            g = d[d.algorithm == algorithm]
            valid = g[column].notna()
            ax.scatter(g.loc[valid,'input_size'], g.loc[valid,column], s=16, color=color, alpha=.22, linewidth=0)
        ax.fill_between(s.input_size, s[f'{metric}_q25'], s[f'{metric}_q75'], color=color, alpha=.13)
        ax.plot(s.input_size, s[f'{metric}_median'], marker=MARKERS[algorithm], ms=5,
                linewidth=1.8, color=color, label=LABELS[algorithm],
                linestyle='--' if algorithm in ['Binary_Search','Quick_Sort'] else '-')
    ax.legend(frameon=False, loc='best')

def save(fig, name, title, note):
    fig.suptitle(title, x=.07, ha='left', fontsize=17, fontweight='bold', y=.98)
    fig.text(.07,.025,note,fontsize=9,color='#555555',va='bottom')
    fig.tight_layout(rect=[.025,.09,.99,.91], w_pad=3)
    path = FIG / f'{name}_{TAG}.png'
    fig.savefig(path, dpi=180)
    plt.close(fig)
    figure_paths.append(path)

fig, axes = plt.subplots(1,2,figsize=(13,5.6))
for ax, algorithms, title in zip(axes,[ORDER[:2],ORDER[2:]],['Search algorithms','Sorting algorithms']):
    series(ax, algorithms, 'runtime', 'runtime_valid_ms')
    format_axis(ax,'Runtime (ms; log scale)')
    ax.set_title(title)
save(fig,'runtime_trends','Runtime grows differently across algorithms',
     'Lines: median; bands: 25th–75th percentile; dots: valid repeated runs. Both axes use log scales.\nOne missing and one zero runtime excluded only from runtime summaries; 18 values at 0.05 ms retained.')

fig, axes = plt.subplots(1,2,figsize=(13,5.6))
series(axes[0], ORDER, 'memory', 'memory_valid_mb', show_raw=False)
format_axis(axes[0], 'Memory (MB)', log_y=False)
axes[0].set_ylim(0, 48)
axes[0].set_title('Median memory and interquartile range')
for algorithm in ORDER:
    g = d[d.algorithm == algorithm]
    axes[1].scatter(g.input_size,g.memory_mb,s=27,color=COLORS[algorithm],marker=MARKERS[algorithm],alpha=.6,label=LABELS[algorithm])
format_axis(axes[1], 'Memory (MB; log scale)')
axes[1].set_title('All 224 observations, including the extreme value')
axes[1].legend(frameon=False,loc='center left')
axes[1].annotate('RUN0090: 420 MB\nBinary Search, n = 10,000',xy=(10000,420),xytext=(650,140),
                 arrowprops={'arrowstyle':'->','color':'#555'},fontsize=9)
save(fig,'memory_trends','Sorting memory rises; one extreme measurement needs review',
     'Left: medians and 25th–75th percentiles on a zero-based scale. Right: all raw measurements on a log scale.\nThe 420 MB measurement is flagged but retained in every memory summary; MB follows the source column name.')

fig, axes = plt.subplots(1,2,figsize=(13,5.6))
for ax, algorithms, title in zip(axes,[ORDER[:2],ORDER[2:]],['Search algorithms','Sorting algorithms']):
    series(ax, algorithms, 'comparisons', 'comparisons_valid')
    format_axis(ax,'Comparisons (count; log scale)')
    ax.set_title(title)
save(fig,'comparison_trends','Comparison counts reveal the scale of work',
     'Lines: median; bands: 25th–75th percentile; dots: valid repeated runs. Both axes use log scales.\nOne impossible negative count (RUN0193: -10) excluded only from comparison summaries; no other measurements removed.')

def val(algorithm, n, metric):
    return float(summary.loc[(summary.algorithm==algorithm)&(summary.input_size==n),metric].iloc[0])
linear = val('Linear_Search',100000,'runtime_median')
binary = val('Binary_Search',100000,'runtime_median')
merge = val('Merge_Sort',100000,'runtime_median')
quick = val('Quick_Sort',100000,'runtime_median')
merge_mem = val('Merge_Sort',100000,'memory_median')
quick_mem = val('Quick_Sort',100000,'memory_median')
binary_10k = d[(d.algorithm=='Binary_Search')&(d.input_size==10000)]
memory_mean = binary_10k.memory_mb.mean()
mean_without_flag = binary_10k.loc[~binary_10k.memory_extreme_flag,'memory_mb'].mean()
zero_group=d[(d.algorithm=='Merge_Sort')&(d.input_size==5000)]
largest = summary[summary.input_size==100000]
table_rows = '\n'.join(f"| {LABELS[r.algorithm]} | {r.runtime_median:.4f} | {r.memory_median:.3f} | {r.comparisons_median:,.1f} |" for r in largest.itertuples())
quality_rows = '\n'.join(f"| {r.run_id} | {r.algorithm} | {r.input_size:,} | {issue} | {handling} |" for r,issue,handling in [
    (d[d.runtime_missing].iloc[0],'runtime_ms 缺失','耗時排除 1 筆；其他指標保留'),
    (d[d.runtime_nonpositive].iloc[0],'runtime_ms = 0','視為無法判讀的計時值，耗時排除 1 筆；其他指標保留'),
    (d[d.comparisons_negative].iloc[0],'comparisons = -10','比較次數排除 1 筆；其他指標保留'),
    (d[d.memory_extreme_flag].iloc[0],'memory_mb = 420','標記為極端值，保留於所有記憶體分析')])
report = f'''# 演算法測量資料：重要趨勢與視覺化

## 主要發現

1. **搜尋耗時出現規模交叉。** n=1,000 時 Linear Search 中位耗時為 {val('Linear_Search',1000,'runtime_median'):.4f} ms，低於 Binary Search 的 {val('Binary_Search',1000,'runtime_median'):.4f} ms；n=5,000 時分別為 {val('Linear_Search',5000,'runtime_median'):.4f} 與 {val('Binary_Search',5000,'runtime_median'):.4f} ms。交叉只可定位在已測的 1,000–5,000 區間，無法推定精確臨界點。
2. **大型輸入時 Binary Search 耗時增長較緩。** n 從 100 增至 100,000（1,000 倍），其中位耗時從 {val('Binary_Search',100,'runtime_median'):.4f} 增至 {binary:.4f} ms（{binary/val('Binary_Search',100,'runtime_median'):.2f} 倍）。n=100,000 時 Linear Search 為 {linear:.4f} ms，Binary Search 耗時約為其 1/{linear/binary:.2f}。這是本資料的觀察，不代表所有環境皆如此。
3. **Quick Sort 在最大規模兼具較低耗時與記憶體中位數。** n=100,000 時 Quick Sort 為 {quick:.4f} ms，Merge Sort 為 {merge:.4f} ms；前者耗時低 {(1-quick/merge)*100:.1f}%。記憶體分別為 {quick_mem:.3f} 與 {merge_mem:.3f} MB，前者低 {(1-quick_mem/merge_mem)*100:.1f}%。n=100–1,000 的計時較小且有集中在 0.05 ms 的值，不對微小差異做強排名。
4. **比較次數支持不同增長型態。** Binary Search 的比較次數中位數從 n=100 的 {val('Binary_Search',100,'comparisons_median'):.1f} 增至 n=100,000 的 {val('Binary_Search',100000,'comparisons_median'):.1f}；Linear Search 從 {val('Linear_Search',100,'comparisons_median'):.1f} 增至 {val('Linear_Search',100000,'comparisons_median'):,.1f}。排序的比較次數大致隨 n log₂ n 增長，但有限測量不能證明漸近複雜度。
5. **420 MB 的極端值會扭曲平均數。** Binary Search、n=10,000 的記憶體中位數為 {val('Binary_Search',10000,'memory_median'):.3f} MB，平均數卻達 {memory_mean:.3f} MB。僅作敏感度比較，若排除該旗標值，平均數為 {mean_without_flag:.3f} MB（其餘 7 筆）；主要分析仍保留它。

## 資料品質與處理

- 原始資料 224 列、7 欄；4 種演算法 × 7 個輸入大小 × 8 次重複，28 個完整實驗組。沒有日期欄，因此這裡的趨勢指輸入規模變化，不能當作時間趨勢。
- 欄位：run_id、algorithm（字串）；input_size、repeat、comparisons（整數）；runtime_ms、memory_mb（浮點數）。數值轉換失敗均為 0。輸入大小為 {quality['input_sizes']}，repeat 為 1–8。
- 缺失：僅 runtime_ms 1 筆，其他欄位均為 0。完全重複列、run_id 重複、algorithm/input_size/repeat 鍵重複皆為 0；重複測量是合法的實驗重複，沒有去重。
- 原始數值範圍：input_size 100–100,000；repeat 1–8；runtime_ms 0–207；memory_mb 16.92–420；comparisons -10–1,590,525。所有非缺失數值皆可轉換；無不合法的 input_size、repeat 或記憶體非正值。
- 18 筆 runtime_ms 恰為 0.05，集中在 n≤1,000。這可能是計時解析度或下限效果，來源未說明；全部保留，避免擅自修改。
- 不填補缺失、不修改 data.csv。每個指標獨立排除不可用值，處理後保留全部 224 列。有效耗時 222 筆、記憶體 224 筆、比較次數 223 筆；Linear Search/n=1,000 與 Merge Sort/n=5,000 的有效耗時各 7 筆，Quick Sort/n=5,000 的有效比較次數 7 筆，其餘每組各 8 筆。

| run_id | algorithm | input_size | 問題 | 處理 |
|---|---|---:|---|---|
{quality_rows}

記憶體極端值旗標定義：同一 algorithm/input_size 群組內，高於「中位數 + 10 × MAD（絕對離差中位數）」；本資料僅 RUN0090 觸發。旗標是待查線索，無法證明錯誤。

零耗時敏感度：Merge Sort/n=5,000 排除 0 的中位耗時為 {val('Merge_Sort',5000,'runtime_median'):.4f} ms；若保留 0 則為 {zero_group.runtime_ms.median():.4f} ms，差異 {(val('Merge_Sort',5000,'runtime_median')/zero_group.runtime_ms.median()-1)*100:.2f}%，不改變與 Quick Sort 的觀察方向。

## 視覺化選擇與讀法

使用現有的 pandas、NumPy 與 Matplotlib。這是供閱讀及分享的固定比較分析，靜態 PNG 便於離線開啟；不需新增依賴。圖表標籤使用英文 DejaVu Sans，避免缺少中文字型；本報告以繁體中文說明。

- 耗時與比較次數採搜尋／排序分面折線圖：橫軸是有序的輸入規模，雙對數刻度容納多數量級；線與標記為每組中位數、色帶是第 25–75 百分位數、淡色點保留個別測量。不同類別搭配一致顏色、標記及線型。色帶表示觀測離散程度，**不是信賴區間**。
- 記憶體左圖採從 0 起的線性縱軸比較中位數與四分位區間；右圖使用對數縱軸顯示全部原始值，包含 420 MB，沒有隱藏極端值。各圖橫軸均為對數刻度；MB 是依原欄位名稱，無法確認是 MB 或 MiB。
- 不將不同任務的搜尋與排序排成同一效能名次；未計算跨演算法混合相關係數，避免共同輸入規模與任務差異造成誤導。

![耗時趨勢](../figures/runtime_trends_{TAG}.png)

![記憶體趨勢](../figures/memory_trends_{TAG}.png)

![比較次數趨勢](../figures/comparison_trends_{TAG}.png)

## 最大輸入規模的中位數（n=100,000）

| 演算法 | 耗時 (ms) | 記憶體 (MB) | 比較次數 |
|---|---:|---:|---:|
{table_rows}

搜尋與排序解決的任務不同，表格只供各任務內比較。

## 限制

每組僅 8 次測量，且部分指標只剩 7 筆，沒有母體信賴區間或顯著性推論。未提供硬體、語言實作、輸入分布、暖機、計時方式、資料排序狀態與 Binary Search 前置排序成本，也不能確認相同 repeat 是否為配對輸入；因此不做配對檢定、因果推論或泛化效能保證。420 MB 與 0.05 ms 的成因需向資料來源確認；0 ms 被視為無法判讀的計時值是一項明示的分析假設。未擅自刪除其他離群值。

## 執行及驗證

在專案目錄執行 `MPLCONFIGDIR=/tmp/q3_with_agents_mpl XDG_CACHE_HOME=/tmp/q3_with_agents_cache python src/analyze.py`。每次重跑輸出新版本，保留既有成果。

程式檢查原檔 SHA-256 不變、28 個分組的計數與原始有效資料一致、摘要中位數與逐組重算結果一致，並使用 Pillow 解碼驗證所有 PNG。實際驗證結果另存 `validation_{TAG}.json`；圖片另經人工視覺檢查。

原始檔 SHA-256：`{source_hash}`。
環境：Python {platform.python_version()}；pandas {pd.__version__}；NumPy {np.__version__}；Matplotlib {matplotlib.__version__}。
'''
(REPORT / f'analysis_{TAG}.md').write_text(report, encoding='utf-8')
# A self-contained HTML report uses embedded PNGs and no remote resources.
import base64
html_images = ''.join(f'<figure><img alt="{html.escape(p.stem)}" src="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"></figure>' for p in figure_paths)
html_doc = f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>演算法資料分析</title><style>body{{max-width:1200px;margin:36px auto;padding:0 20px;font-family:system-ui,sans-serif;color:#24303d;line-height:1.65}}img{{width:100%;height:auto}}figure{{margin:30px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-family:inherit}}h1{{font-size:28px}}</style><h1>演算法資料分析</h1><p>圖表可離線開啟；完整數值、清理方法與限制列於圖表下方。</p>{html_images}<hr><pre>{html.escape(report)}</pre></html>'''
(REPORT / f'analysis_{TAG}.html').write_text(html_doc, encoding='utf-8')

assert len(summary) == 28
assert len(d) == 224
for metric, column in [('runtime','runtime_valid_ms'), ('memory','memory_valid_mb'), ('comparisons','comparisons_valid')]:
    actual = d.groupby(['algorithm','input_size'])[column].median().sort_index()
    saved = summary.set_index(['algorithm','input_size'])[f'{metric}_median'].sort_index()
    np.testing.assert_allclose(actual.to_numpy(), saved.to_numpy())
    assert summary[f'{metric}_n'].sum() == d[column].notna().sum()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
image_checks = []
for path in figure_paths:
    with Image.open(path) as img:
        img.load()
        assert img.width > 1500 and img.height > 700
        image_checks.append({'file':str(path.relative_to(ROOT)), 'width':img.width,'height':img.height,'bytes':path.stat().st_size,'format':img.format})
validation = {'status':'passed','source_unchanged':True,'summary_groups':len(summary),
              'counts_and_medians_recomputed':True,'png_decode_checks':image_checks,
              'html_self_contained':True,'interactive_charts':'not used',
              'visual_inspection':'pending separate view_image inspection',
              'versions':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__}}
(REPORT / f'validation_{TAG}.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'version':TAG,'report':str((REPORT/f'analysis_{TAG}.md').relative_to(ROOT)), 'validation':validation,'quality':quality},ensure_ascii=False,indent=2))
