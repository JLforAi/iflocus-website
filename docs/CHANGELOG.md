# 網站變更紀錄

記錄會影響數據解讀（GA4 事件、效能指標等）的網站行為變更。本檔位於 docs/，不會被發布。

## 2026-10-26

- 3D demo 改為首次互動載入（iflocusOMO、ailocus、sports-marketing 首支 demo）：使用者第一次 scroll／touchstart／pointerdown／wheel／keydown 才載入，載入前顯示海報。PR #102。
  - 之後比較 demo 相關 GA4 事件數時，以這天為分界：此後 demo 事件只來自「有互動過的訪客」，與之前的數字不可直接比較。

## 2026-10-27

- 3D demo 改為首次渲染後淡入，移除保險計時器（iflocusOMO、ailocus、sports-marketing 首支 demo）：互動後 iframe 先保持透明、海報持續顯示，demo 畫出第一個畫面後以 postMessage 通知外層才淡入；不支援 WebGL 時維持顯示海報。
- 首頁數字區改為「300 萬 單次最大推送」，來源：Joseph 2026-10-27 確認此推送量目前仍可達成（含合作夥伴量）。
