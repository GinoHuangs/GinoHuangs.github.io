from pathlib import Path
import hashlib
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/question1_mpl_cache")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/question1_cache")
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
def fresh(path):
    candidate = path
    version = 2
    while candidate.exists():
        candidate = path.with_name(f'{path.stem}_v{version}{path.suffix}')
        version += 1
    return candidate

from matplotlib import font_manager
font_path = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
    font_name = font_manager.FontProperties(fname=str(font_path)).get_name()
else:
    font_name = 'Noto Sans CJK TC'
sns.set_theme(style='whitegrid', font=font_name)
plt.rcParams['axes.unicode_minus'] = False
quality = {}
hashes = {}
frames = []
for path in sorted((ROOT/'data/raw').glob('*.csv')):
    hashes[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    df = pd.read_csv(path)
    key = df.columns[0]
    numeric = df.select_dtypes('number')
    quality[path.name] = {
        'rows': len(df), 'columns': list(df.columns),
        'types': df.dtypes.astype(str).to_dict(),
        'missing': df.isna().sum().to_dict(),
        'duplicate_rows': int(df.duplicated().sum()),
        'duplicate_ids': int(df[key].duplicated().sum()),
        'numeric_ranges': {c: [float(numeric[c].min()), float(numeric[c].max())] for c in numeric},
        'negative_numeric_counts': (numeric < 0).sum().to_dict(),
        'categories': {c: sorted(df[c].dropna().unique().tolist()) for c in df.select_dtypes('object') if c != key and df[c].nunique() <= 20}
    }
    frames.append(df)
a, s, w = frames
assert len(frames) == 3
assert not a['run_id'].duplicated().any()
assert not s['module_id'].duplicated().any()
assert not w['request_id'].duplicated().any()
assert a['input_size'].gt(0).all()
assert a[['runtime_ms','memory_mb']].dropna().ge(0).all().all()
invalid_comparisons = int(a['comparisons'].lt(0).sum())
a.loc[a['comparisons'].lt(0), 'comparisons'] = float('nan')
a.to_csv(fresh(ROOT/'data/processed/algorithm_checked.csv'), index=False)
assert s['test_coverage_pct'].between(0,100).all()
assert s.select_dtypes('number').ge(0).all().all()
assert w[['latency_ms','response_kb']].ge(0).all().all()
assert w['status_code'].between(100,599).all()
w['timestamp'] = pd.to_datetime(w['timestamp'], errors='coerce')
assert w['timestamp'].notna().all()
assert w['cache_hit'].dtype == bool

# Exclude the missing runtime only from runtime analysis, never impute zero.
ar = a.dropna(subset=['runtime_ms'])
ar.to_csv(fresh(ROOT/'data/processed/algorithm_runtime_valid.csv'), index=False)
g = ar.groupby(['algorithm','input_size'])['runtime_ms'].agg(['mean','std','count']).reset_index()
g.to_csv(fresh(ROOT/'data/processed/algorithm_runtime_summary.csv'), index=False)
fig, axes = plt.subplots(1,2, figsize=(13,5.5), layout='constrained')
colors = ['#0072B2','#D55E00']
for ax, names, title in zip(axes, [['Linear_Search','Binary_Search'],['Merge_Sort','Quick_Sort']], ['搜尋演算法','排序演算法']):
    for name, color, marker in zip(names, colors, ['o','s']):
        v = g[g.algorithm == name].sort_values('input_size')
        ax.errorbar(v.input_size, v['mean'], yerr=v['std'], marker=marker, color=color, label=name, capsize=3)
    ax.set_xscale('log')
    ax.set(xlabel='輸入大小（筆，對數尺度）', ylabel='平均執行時間（毫秒）', title=title)
    ax.legend()
fig.suptitle('演算法效能：依輸入大小比較\n誤差棒為樣本標準差；執行時間缺失值僅從此分析排除', fontsize=14)
fig.savefig(fresh(ROOT/'outputs/figures/algorithm_runtime.png'), dpi=180)
plt.close(fig)

fig, axes = plt.subplots(1,2, figsize=(13,5.5), layout='constrained')
sns.boxplot(data=s, x='module_type', y='test_coverage_pct', color='#56B4E9', ax=axes[0])
axes[0].set(title='各模組類型的測試覆蓋率', xlabel='模組類型', ylabel='測試覆蓋率（%）')
cols = ['LOC','code_churn_lines','cyclomatic_complexity','test_coverage_pct','defect_count','review_time_hours','contributors']
corr = s[cols].corr(method='spearman')
sns.heatmap(corr, annot=True, fmt='.2f', cmap='vlag', vmin=-1, vmax=1, center=0, ax=axes[1], annot_kws={'size':8}, cbar_kws={'label':'Spearman 相關係數'})
axes[1].set_title('品質指標相關性（不代表因果）')
axes[1].tick_params(axis='x', rotation=65, labelsize=8)
axes[1].tick_params(axis='y', labelsize=8)
fig.suptitle('軟體品質：分布比較與相關性分析', fontsize=15)
fig.savefig(fresh(ROOT/'outputs/figures/software_quality.png'), dpi=180)
plt.close(fig)
corr.to_csv(fresh(ROOT/'data/processed/software_spearman_correlation.csv'))

w['hour'] = w['timestamp'].dt.floor('h')
hourly = w.groupby('hour').size()
endpoints = w.groupby('endpoint')['latency_ms'].agg(median='median', p95=lambda x:x.quantile(.95)).sort_values('p95')
endpoints.to_csv(fresh(ROOT/'data/processed/web_endpoint_latency.csv'))
fig, axes = plt.subplots(1,3, figsize=(16,5.5), layout='constrained')
axes[0].plot(hourly.index, hourly.values, color='#0072B2', marker='o', markersize=3)
axes[0].xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m-%d %H:%M'))
axes[0].tick_params(axis='x', rotation=45)
axes[0].set(title='每小時請求量', xlabel='紀錄時間（原始資料未註明時區）', ylabel='請求數（筆）')
x = range(len(endpoints))
axes[1].bar([i-.2 for i in x], endpoints['median'], width=.4, label='中位數', color='#0072B2')
axes[1].bar([i+.2 for i in x], endpoints['p95'], width=.4, label='第 95 百分位數', color='#D55E00', hatch='//')
axes[1].set_xticks(list(x), endpoints.index, rotation=45, ha='right')
axes[1].set(title='端點延遲比較', xlabel='端點', ylabel='延遲（毫秒）')
axes[1].legend()
sns.boxplot(data=w, x='cache_hit', y='latency_ms', color='#56B4E9', ax=axes[2])
axes[2].set(title='快取命中與延遲分布', xlabel='快取命中', ylabel='延遲（毫秒）')
fig.suptitle('網站服務：流量、端點延遲與快取分布\n保留全部 2,500 筆請求；離群點不直接刪除', fontsize=14)
fig.savefig(fresh(ROOT/'outputs/figures/web_service.png'), dpi=180)
plt.close(fig)

for path, before in hashes.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
for path in (ROOT/'outputs/figures').glob('*.png'):
    with Image.open(path) as img:
        img.verify()
    assert path.stat().st_size > 0
fresh(ROOT/'outputs/reports/data_quality.json').write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding='utf-8')
large = g[g.input_size == g.input_size.max()]
coverage = s.groupby('module_type')['test_coverage_pct'].median()
cache = w.groupby('cache_hit')['latency_ms'].median()
errors = int(w.status_code.ge(400).sum())
report = f'''# 問題 1：實際測試 AGENTS.md

## 測試任務
「請分析這份資料，並製作適合的資料視覺化。」

以既有 AGENTS.md 規範分析三份 CSV，依圖片交付需求選擇靜態圖。
本次為同一 Agent 讀取規範後的實作測試，並非另一個獨立 Agent 的盲測。

## 五項要求與實測證據
| 要求 | 結果與證據 |
|---|---|
| 主動檢查資料 | 三份資料的欄位、型別、缺失、重複列、重複識別碼、範圍及負值檢查記錄於 data_quality.json。完成覆蓋率、狀態碼、日期及非負數值驗證。 |
| 選擇適合 package | Matplotlib 用於誤差棒與多圖版面；Seaborn 用於箱型圖與相關熱圖。此次需要靜態圖片，未強制使用 Plotly。 |
| 選擇適合圖表 | 演算法使用分組折線與標準差誤差棒；品質使用箱型圖及 Spearman 熱圖；網站使用時間折線、延遲長條圖與箱型圖。 |
| 遵守圖表格式 | 圖表具標題、軸名稱與單位，使用中文字型；多系列提供圖例、標記或紋理；演算法輸入軸標示對數尺度。 |
| 正確輸出成果 | 三組 PNG 使用 180 dpi；彙整 CSV、檢查 JSON 與本報告均已輸出；PNG 解碼檢查通過。 |

## 資料處理
- 演算法：{len(a)} 筆；runtime_ms 缺失 {int(a.runtime_ms.isna().sum())} 筆。僅在執行時間分析排除該筆，不填 0，不從其他資料刪除；各組以有效測量計算平均、樣本標準差與筆數。
- 比較次數有 {invalid_comparisons} 筆負值（原值 -10），在處理後資料標為缺失，不參與比較次數統計；其有效執行時間仍保留。
- 軟體品質：{len(s)} 筆。以箱型圖保留離群點；熱圖排除 module_id，使用 Spearman 相關係數。
- 網站紀錄：{len(w)} 筆。時間欄轉換成功；依小時彙整請求量，依端點計算延遲中位數與 P95，未抽樣。時間未附時區，不自行假定。
- 完全重複列與重複識別碼請見 JSON；未自動移除觀測值。原始 CSV 的 SHA-256 前後一致。

## 觀察結果
- 最大輸入大小的平均執行時間（毫秒）：{large.set_index('algorithm')['mean'].round(3).to_dict()}。搜尋與排序分開比較，避免將不同任務解讀為共同排名。
- 各模組類型的測試覆蓋率中位數（%）：{coverage.round(2).to_dict()}。
- 複雜度與缺陷數的 Spearman 相關係數：{corr.loc['cyclomatic_complexity','defect_count']:.3f}；此結果不能證明因果關係。
- P95 最高的端點為 {endpoints.p95.idxmax()}，P95 為 {endpoints.p95.max():.2f} 毫秒。
- 快取未命中／命中的延遲中位數（毫秒）：{cache.round(2).to_dict()}；組別差異可能受端點與其他因素影響。
- HTTP 狀態碼 >= 400 的請求為 {errors}/{len(w)}，占 {errors/len(w):.2%}。

## 驗證與限制
- 實際執行 Python 分析並完成資料合理性斷言、輸出 PNG 解碼及原始檔案完整性檢查。
- 圖片另經視覺檢查；檢查結果記錄於 visual_review.md。
- 無互動 HTML，因此互動功能不屬於本次驗證範圍。
- 僅憑 CSV 無法確認原始資料的量測方法與真實性；結果只代表提供的資料。
- 本次未在全新環境重建依賴，不能宣稱已完成跨環境重現測試。
'''
fresh(ROOT/'outputs/reports/question1_test_report.md').write_text(report, encoding='utf-8')
fresh(ROOT/'README.md').write_text('''# 問題 1：資料視覺化實測

從本資料夾執行：

```bash
python3 src/test_question1.py
```

使用 Python、pandas、Matplotlib、Seaborn、Pillow；中文字型為 Noto Sans CJK TC。
原始 CSV 在 data/raw/，圖片在 outputs/figures/，測試報告在 outputs/reports/。
重跑時輸出以版本號另存，不覆寫既有成果。
''', encoding='utf-8')
print(report)
print('Versions:',pd.__version__,matplotlib.__version__,sns.__version__)
