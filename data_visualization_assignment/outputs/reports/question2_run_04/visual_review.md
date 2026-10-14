# 視覺檢查

已逐張檢視 A、B、C 圖及 D 的 d_interactive_explorer_clean.png。
中文、軸標籤、圖例皆可讀，無截斷或缺字；A 搜尋與排序分開，B 不宣稱因果，C 明示 IQR 規則與候選數。
D 初次截圖出現 Plotly 操作提示遮住部分圖例，已另產生 clean 圖供正式使用，未修改原圖。
D 的 hover、圖例切換及拖曳縮放已在 Chromium 實測通過，見 interactive_validation.json。
實作過程修正瀏覽器 file:// 存取限制（改用內部 HTTP）、主圖與範圍滑桿重複計點及 SVG 文字讀取方式；最終驗證完成。
