from pathlib import Path
import os, sys, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.deps'))
os.environ.setdefault('MPLCONFIGDIR','/tmp/question2_mpl')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/question2_cache')
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import seaborn as sns
import plotly, plotly.graph_objects as go
from PIL import Image
from playwright.sync_api import sync_playwright
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font_manager.fontManager.addfont(font)
sns.set_theme(style='whitegrid',font=font_manager.FontProperties(fname=font).get_name())
plt.rcParams['axes.unicode_minus']=False
run=1
while (ROOT/f'outputs/reports/question2_run_{run:02d}').exists(): run+=1
name=f'question2_run_{run:02d}'
figdir=ROOT/'outputs/figures'/name
reportdir=ROOT/'outputs/reports'/name
htmldir=ROOT/'outputs/html'/name
proc=ROOT/'data/processed'/name
for p in [figdir,reportdir,htmldir,proc]: p.mkdir(parents=True)
raw=sorted((ROOT/'data/raw').glob('*.csv'))
hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in raw}
a,s,w=[pd.read_csv(p) for p in raw]
quality={}
for p,d in zip(raw,[a,s,w]):
 n=d.select_dtypes('number')
 quality[p.name]={'rows':len(d),'columns':list(d),'types':d.dtypes.astype(str).to_dict(),'missing':d.isna().sum().to_dict(),'duplicates':int(d.duplicated().sum()),'duplicate_ids':int(d.iloc[:,0].duplicated().sum()),'ranges':{c:[float(n[c].min()),float(n[c].max())] for c in n},'negative_counts':n.lt(0).sum().to_dict()}
assert s.test_coverage_pct.between(0,100).all()
assert w.status_code.between(100,599).all()
assert w[['latency_ms','response_kb']].ge(0).all().all()
w.timestamp=pd.to_datetime(w.timestamp,errors='coerce')
assert w.timestamp.notna().all()
(reportdir/'data_quality.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2))
# A: performance trends; invalid comparisons do not invalidate runtime.
runtime=a[a.runtime_ms.notna() & a.runtime_ms.ge(0) & a.input_size.gt(0)]
g=runtime.groupby(['algorithm','input_size']).runtime_ms.agg(['mean','std','count']).reset_index()
g.to_csv(proc/'a_runtime_summary.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(13,5.5),layout='constrained')
for ax,names,title in zip(axes,[['Linear_Search','Binary_Search'],['Merge_Sort','Quick_Sort']],['搜尋演算法','排序演算法']):
 for alg,color,marker in zip(names,['#0072B2','#D55E00'],['o','s']):
  v=g[g.algorithm.eq(alg)]
  ax.errorbar(v.input_size,v['mean'],yerr=v['std'],label=alg,color=color,marker=marker,capsize=3)
 ax.set_xscale('log'); ax.set(title=title,xlabel='輸入大小（筆，對數尺度）',ylabel='平均執行時間（毫秒）'); ax.legend()
fig.suptitle('任務 A｜效能成長趨勢\n誤差棒：樣本標準差；缺失時間不填 0',fontsize=15)
fig.savefig(figdir/'a_performance_trend.png',dpi=180);plt.close(fig)
# B: association, all observations and sample size.
rho=s[['cyclomatic_complexity','defect_count']].corr(method='spearman').iloc[0,1]
fig,axes=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
sns.scatterplot(data=s,x='cyclomatic_complexity',y='defect_count',hue='language',style='language',alpha=.65,ax=axes[0])
axes[0].set(title=f'複雜度與缺陷數｜Spearman ρ = {rho:.3f}',xlabel='循環複雜度（分數）',ylabel='缺陷數（個）')
axes[0].legend(title='程式語言')
sns.boxplot(data=s,x='defect_count',y='cyclomatic_complexity',color='#56B4E9',ax=axes[1])
axes[1].set(title='依缺陷數觀察複雜度分布',xlabel='缺陷數（個）',ylabel='循環複雜度（分數）')
fig.suptitle(f'任務 B｜變數關係（n = {len(s)}）\n相關性不代表因果關係；保留全部觀測值',fontsize=15)
fig.savefig(figdir/'b_variable_relationship.png',dpi=180);plt.close(fig)
# C: endpoint-specific Tukey fences, retain outliers.
threshold=w.groupby('endpoint').latency_ms.quantile([.25,.75]).unstack()
threshold.columns=['q1','q3'];threshold['iqr']=threshold.q3-threshold.q1
threshold['lower']=threshold.q1-1.5*threshold.iqr;threshold['upper']=threshold.q3+1.5*threshold.iqr
wc=w.join(threshold,on='endpoint')
wc['is_outlier']=(wc.latency_ms<wc.lower)|(wc.latency_ms>wc.upper)
out=wc[wc.is_outlier].sort_values('latency_ms',ascending=False)
out.to_csv(proc/'c_latency_outliers.csv',index=False);threshold.to_csv(proc/'c_iqr_thresholds.csv')
fig,axes=plt.subplots(1,2,figsize=(13,5.5),layout='constrained')
order=threshold.index.tolist()
sns.boxplot(data=wc,x='endpoint',y='latency_ms',order=order,color='#56B4E9',ax=axes[0])
axes[0].set(title='依端點分組的延遲分布',xlabel='端點',ylabel='延遲（毫秒）')
axes[0].tick_params(axis='x',rotation=30)
counts=wc.groupby('endpoint').is_outlier.sum().reindex(order)
axes[1].bar(order,counts,color='#D55E00')
for i,c in enumerate(counts): axes[1].text(i,c+.2,str(c),ha='center')
axes[1].set(title=f'異常候選共 {len(out)} 筆／{len(wc)} 筆',xlabel='端點',ylabel='超出 IQR 界線的請求數（筆）',ylim=(0,max(counts)*1.18+1))
axes[1].tick_params(axis='x',rotation=30)
fig.suptitle('任務 C｜異常延遲探索\n各端點獨立使用 Q1 − 1.5×IQR 與 Q3 + 1.5×IQR；異常候選不等於錯誤',fontsize=14)
fig.savefig(figdir/'c_latency_outliers.png',dpi=180);plt.close(fig)
# D: all individual requests, embedded Plotly library, browser-tested.
f=go.Figure()
colors=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9']
for endpoint,color,symbol in zip(order,colors,['circle','square','diamond','cross','triangle-up','x']):
 d=wc[wc.endpoint.eq(endpoint)].sort_values('timestamp')
 custom=[[str(r.request_id),int(r.status_code),str(r.region),str(r.device),str(r.cache_hit),bool(r.is_outlier)] for r in d.itertuples()]
 f.add_trace(go.Scatter(x=d.timestamp.dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),y=d.latency_ms.tolist(),mode='markers',name=endpoint,marker={'size':7,'opacity':.65,'color':color,'symbol':symbol},customdata=custom,hovertemplate='端點：'+endpoint+'<br>時間：%{x}<br>延遲：%{y:.1f} ms<br>請求：%{customdata[0]}<br>狀態碼：%{customdata[1]}<br>地區：%{customdata[2]}<br>裝置：%{customdata[3]}<br>快取：%{customdata[4]}<br>IQR 異常候選：%{customdata[5]}<extra></extra>'))
f.update_layout(title='任務 D｜網站請求互動探索（2,500 筆）<br><sup>滑鼠查看單筆資料｜拖曳縮放｜點擊圖例切換端點｜雙擊重設</sup>',font={'family':'Noto Sans CJK JP, sans-serif','size':15},template='plotly_white',height=800,xaxis_title='紀錄時間（原始資料未註明時區）',yaxis_title='延遲（毫秒）',legend_title_text='端點',hovermode='closest',xaxis={'rangeslider':{'visible':True}},margin={'t':110,'b':100})
html=htmldir/'d_web_service_explorer.html'
f.write_html(html,include_plotlyjs=True,full_html=True,config={'scrollZoom':True,'displaylogo':False,'toImageButtonOptions':{'format':'png','scale':2}})
assert sum(len(t.x) for t in f.data)==len(w)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(htmldir)))
Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1500,'height':920},device_scale_factor=2)
 errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(f'http://127.0.0.1:{server.server_port}/{html.name}');page.wait_for_selector('.scatterlayer .point');page.evaluate('document.fonts.ready')
 assert page.locator('.scatterlayer').first.locator('.point').count()==2500
 point=page.locator('.scatterlayer .point').first
 point.hover(force=True)
 page.wait_for_selector('.hoverlayer .hovertext')
 hover=page.locator('.hoverlayer').text_content()
 assert 'REQ' in hover and '狀態碼' in hover
 page.mouse.move(5,5)
 page.locator('.legendtoggle').first.click()
 page.wait_for_timeout(400)
 assert page.evaluate("document.querySelector('.plotly-graph-div').data[0].visible")=='legendonly'
 page.locator('.legendtoggle').first.click();page.wait_for_timeout(400)
 before=page.evaluate("document.querySelector('.plotly-graph-div')._fullLayout.xaxis.range.slice()")
 box=page.locator('.nsewdrag').first.bounding_box()
 page.mouse.move(box['x']+box['width']*.2,box['y']+box['height']*.2)
 page.mouse.down();page.mouse.move(box['x']+box['width']*.65,box['y']+box['height']*.8,steps=12);page.mouse.up();page.wait_for_timeout(400)
 after=page.evaluate("document.querySelector('.plotly-graph-div')._fullLayout.xaxis.range.slice()")
 assert before!=after
 page.evaluate("Plotly.relayout(document.querySelector('.plotly-graph-div'), {'xaxis.autorange':true, 'yaxis.autorange':true})")
 page.mouse.move(5,5);page.wait_for_timeout(500)
 page.locator('.notifier').evaluate_all('(nodes) => nodes.forEach(n => n.remove())')
 page.screenshot(path=str(figdir/'d_interactive_explorer.png'),full_page=True)
 assert not errors,errors
 browser.close()
server.shutdown();server.server_close()
verification={'hover_details':True,'legend_toggle':True,'drag_zoom':True,'rendered_points':2500,'javascript_errors':errors,'plotly_version':plotly.__version__}
(reportdir/'interactive_validation.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2))
for path,h in hashes.items():assert hashlib.sha256(path.read_bytes()).hexdigest()==h
for path in figdir.glob('*.png'):
 with Image.open(path) as im:im.verify()
# Browser screenshot is 2x CSS pixel resolution (~192 DPI), label explicitly.
report=f'''# 問題 2：同一份 AGENTS.md 的四種視覺化任務

依 A → B → C → D 實際執行，同一份 AGENTS.md 未修改。資料品質完整記錄於 data_quality.json。原始 CSV SHA-256 前後相同。

## A：觀察效能趨勢
- 任務：分析演算法執行時間如何隨輸入大小變化。
- 工具：Matplotlib；以折線與樣本標準差誤差棒呈現重複測量，搜尋與排序分開。
- 224 筆中執行時間缺失 1 筆，時間分析使用 {len(runtime)} 筆，不填 0；輸入大小皆為正，使用對數 X 軸。
- comparisons 有 1 筆負值，不用於本次時間分析，不因此刪除有效 runtime。
- 最大輸入大小時各演算法平均時間（毫秒）：{g[g.input_size.eq(g.input_size.max())].set_index('algorithm')['mean'].round(3).to_dict()}。

## B：尋找變數關係
- 任務：探索複雜度與缺陷數的關係。
- 工具：Seaborn；散佈圖依語言以顏色和形狀分組，搭配缺陷數分組箱型圖。
- 使用全部 {len(s)} 筆。Spearman ρ = {rho:.3f}，為弱正相關，不能據此推論因果。

## C：探索異常資料
- 任務：尋找各端點特別高或低的延遲。
- 工具：Seaborn + Matplotlib；端點分組箱型圖與異常候選數長條圖。
- 各端點獨立計算 Q1、Q3，超出 Q1−1.5×IQR 或 Q3+1.5×IQR 判為候選；避免用同一門檻混合不同服務。
- 共 {len(out)} / {len(w)} 筆（{len(out)/len(w):.2%}）候選，低延遲候選 {int((wc.latency_ms<wc.lower).sum())} 筆、高延遲候選 {int((wc.latency_ms>wc.upper).sum())} 筆，保留原資料，不直接刪除。
- 最高延遲請求：{out.iloc[0].request_id}，端點 {out.iloc[0].endpoint}，延遲 {out.iloc[0].latency_ms:.1f} 毫秒。
- 完整候選與門檻另存 CSV；異常候選不等於資料錯誤。

## D：互動式資料探索
- 任務：讓使用者 hover、zoom 並查看單筆請求細節。
- 新增 Plotly {plotly.__version__} 於專案 .deps，未升級既有環境套件。
- HTML 內嵌 JavaScript，保留全部 2,500 筆，hover 顯示 ID、狀態碼、地區、裝置、快取及異常標記。
- Chromium 實際驗證：2,500 點渲染、hover 細節、圖例切換、拖曳縮放均通過，無 JavaScript 錯誤。
- PNG 是實際互動圖的瀏覽器截圖；互動操作請開啟 HTML。

## 驗證與限制
- A/B/C PNG 為 180 dpi；D 瀏覽器截圖以 2 倍像素輸出，供報告展示。
- 輸出 PNG 均可解碼，原始資料未修改。圖片視覺檢查另見 visual_review.md。
- 資料時間未註明時區，不擅自指定；觀測關係不代表因果，IQR 只是探索規則。
- 本次是同一 Agent 實作，未聲稱獨立 Agent 盲測或全新環境重建。

## 執行
從專案根目錄執行 `python3 src/question2_tasks.py`。
需要既有 pandas、Matplotlib、Seaborn、Pillow、Playwright 及 Chromium；Plotly 安裝於 .deps。
重跑將建立新的 run 資料夾，保留既有成果。
'''
(reportdir/'question2_report.md').write_text(report,encoding='utf-8')
print(report)
print('OUTPUT',name)
