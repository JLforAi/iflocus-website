# 網站變更紀錄

記錄會影響數據解讀（GA4 事件、效能指標等）的網站行為變更。本檔位於 docs/，不會被發布。

## 2026-10-26

- 3D demo 改為首次互動載入（iflocusOMO、ailocus、sports-marketing 首支 demo）：使用者第一次 scroll／touchstart／pointerdown／wheel／keydown 才載入，載入前顯示海報。PR #102。
  - 之後比較 demo 相關 GA4 事件數時，以這天為分界：此後 demo 事件只來自「有互動過的訪客」，與之前的數字不可直接比較。
