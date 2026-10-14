"""Build a self-contained Chinese HTML/PDF submission from verified reports."""
from pathlib import Path
import base64
import html
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/reports/submission'

def inline(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    return re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)

def markdown(text):
    result=[];table=False;code=False;buffer=[]
    for line in text.splitlines():
        if line.startswith('```'):
            if code:result.append('<pre>'+html.escape('\n'.join(buffer))+'</pre>');buffer=[]
            code=not code
            continue
        if code:buffer.append(line);continue
        if line.startswith('|'):
            if re.match(r'^\|[\s:|\-]+\|$',line):continue
            if not table:result.append('<table>');table=True
            cells=line.strip().strip('|').split('|')
            result.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in cells)+'</tr>')
            continue
        if table:result.append('</table>');table=False
        if not line.strip():continue
        match=re.match(r'^(#{1,6})\s+(.*)',line)
        if match:
            level=min(len(match[1])+1,4);result.append(f'<h{level}>'+inline(match[2])+f'</h{level}>')
        elif line.startswith('- '):result.append('<p class="bullet">• '+inline(line[2:])+'</p>')
        else:result.append('<p>'+inline(line)+'</p>')
    if table:result.append('</table>')
    return '\n'.join(result)

def report(title,path):
    return '<section class="chapter"><h1>'+html.escape(title)+'</h1>'+markdown(path.read_text())+'</section>'

def figure(title,path,note=''):
    uri='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
    return '<section class="figurepage"><h1>'+html.escape(title)+'</h1><img src="'+uri+'"><p>'+html.escape(note)+'</p></section>'

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    out=OUT/'questions_1_2_3.html';pdf=OUT/'questions_1_2_3.pdf'
    if out.exists() or pdf.exists():raise FileExistsError('Submission already exists; preserve or version it before rebuilding.')
    parts=['''<section class="cover"><div class="eyebrow">DATA VISUALIZATION · AGENTS.md</div><h1>資料視覺化專題<br>問題 1–3 成果報告</h1><p class="lead">規範實測 → 四類任務 → 有／無規範比較</p><div class="card"><h2>提交範圍</h2><p>問題 1：依規範檢查資料、選工具及圖表、輸出成果。</p><p>問題 2：A 效能趨勢、B 變數關係、C 異常探索、D 互動探索。</p><p>問題 3：兩個獨立 Agent，使用相同資料與 Prompt，依序比較無／有 AGENTS.md。</p></div><p>本報告由實際執行結果整理；不將相關性視為因果，不預設加入規範一定改善所有指標。</p><p>姓名、學號與組別：請小組於繳交前補填。</p></section>''']
    parts.append(report('問題 1｜規範實測',ROOT/'outputs/reports/question1_test_report_v2.md'))
    for title,file in [('演算法效能','algorithm_runtime_v2.png'),('軟體品質','software_quality_v2.png'),('網站服務','web_service_v2.png')]:
        parts.append(figure('問題 1｜'+title,ROOT/'outputs/figures'/file))
    parts.append(report('問題 2｜四種視覺化任務',ROOT/'outputs/reports/question2_run_04/question2_report.md'))
    for label,file in [('A 效能趨勢','a_performance_trend.png'),('B 變數關係','b_variable_relationship.png'),('C 異常探索','c_latency_outliers.png'),('D 互動探索','d_interactive_explorer_clean.png')]:
        parts.append(figure('問題 2｜'+label,ROOT/'outputs/figures/question2_run_04'/file,'D 的互動操作請另開隨附 HTML；PDF 中為靜態截圖。' if label.startswith('D') else ''))
    parts.append(report('問題 3｜有／無 AGENTS.md 比較',ROOT/'outputs/reports/question3/comparison_report.md'))
    index=ROOT/'outputs/reports/question3/figure_index.json'
    import json
    for entry in json.loads(index.read_text()):
        parts.append(figure(entry['title'],ROOT/entry['path'],entry.get('note','')))
    parts.append(report('附錄｜本次共用規範',ROOT/'AGENTS.md'))
    css='''@page {size:A4;margin:18mm 16mm;}*{box-sizing:border-box}body{font-family:"Noto Sans CJK TC","Noto Sans CJK JP",sans-serif;color:#182a3a;font-size:10pt;line-height:1.65;margin:0}h1{font-size:22pt;color:#174a62;line-height:1.35;margin:0 0 8mm}h2{font-size:14pt;margin-top:6mm;color:#174a62}h3,h4{font-size:11pt;margin-bottom:2mm}p{margin:2mm 0}code{font-family:monospace;font-size:8.5pt;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;font-size:8.5pt;margin:4mm 0}td{border:1px solid #cbd7dd;padding:2.3mm;vertical-align:top;overflow-wrap:anywhere}tr:first-child{background:#eaf3f7;font-weight:bold}tr{break-inside:avoid}.chapter,.figurepage{break-before:page}.figurepage{break-inside:avoid}.figurepage img{max-width:100%;max-height:225mm;object-fit:contain}.figurepage p{color:#526a77;font-size:9pt}.cover{padding-top:23mm;min-height:245mm}.cover h1{font-size:32pt;margin:10mm 0}.eyebrow{letter-spacing:2px;color:#26758c;font-size:10pt}.lead{font-size:15pt;color:#526a77}.card{border-left:4px solid #26758c;background:#eef5f7;padding:5mm 7mm;margin:12mm 0}.bullet{padding-left:3mm}pre{white-space:pre-wrap;background:#f2f5f7;padding:4mm;font-size:9pt}h1,h2,h3,h4{break-after:avoid}'''
    out.write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>問題 1–3 成果報告</title><style>'+css+'</style><body>'+''.join(parts)+'</body></html>')
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(OUT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            page=browser.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/{out.name}')
            page.evaluate('document.fonts.ready')
            page.pdf(path=str(pdf),format='A4',print_background=True,display_header_footer=True,header_template='<span></span>',footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#607d8b">資料視覺化專題　·　<span class="pageNumber"></span> / <span class="totalPages"></span></div>')
            browser.close()
    finally:server.shutdown();server.server_close()
    from pypdf import PdfReader
    reader=PdfReader(pdf)
    assert len(reader.pages)>5
    assert all(page.extract_text().strip() for page in reader.pages)
    print(f'Created {pdf} ({len(reader.pages)} pages)')

if __name__=='__main__':build()
