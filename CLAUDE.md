# iflocus-website — Claude Code 專案規則

## PR 截圖驗收規則

**適用範圍**：任何改到 `.html` / `.css` / `.js` / 圖片檔的 PR，都必須附截圖作為完成證據。只改文件（`.md`）、設定檔（不影響頁面渲染）的 PR 可免附。

**工具**：一律使用已安裝的全域 skill `playwright-browser`（headless Playwright），對本地靜態伺服器（例如 `python -m http.server` 或專案既有的 local server）量測，不使用使用者的 Chrome。
若 shell 找不到 `node`，直接用完整路徑呼叫，例如 `C:\Program Files\nodejs\node.exe`。

**頁面範圍**：
- 被修改的頁面本身，加上首頁（`index.html`）。
- 若改到共用檔（全站共用 CSS、`js/components.js` 等會影響多頁面的檔案），站上全部頁面都要跑一次手機版截圖，不限於本次 PR 修改的頁面。

**尺寸**：
- 桌機：1440×900
- 手機：390×844

**前後對照**：每個「頁面 × 尺寸」組合，各截一張 `main`（修改前）版本、一張 branch（修改後）版本。

**存放位置**：截圖存在 repo 外的 `C:\Users\ljose\iflocus-shots\<branch 名稱>\`，**不 commit 進 repo**。
清理：每次開始新的 iflocus 任務前，檢查 `C:\Users\ljose\iflocus-shots\` 下各資料夾，對應 branch 已 merge 或已關閉的，整個資料夾刪除；仍在進行中的 PR 保留。

**回報格式**：PR 描述中附「截圖對照表」，逐列列出：

| 頁面 | 尺寸 | 修改前截圖路徑 | 修改後截圖路徑 | 畫面有差異？ | HTTP 狀態 | Console 錯誤數 |
|---|---|---|---|---|---|---|

並針對每一個有差異的畫面，逐一說明該差異是否為預期（對應本次改動的目的）。

**發現非預期差異時**：先停下，不開 PR，回報給使用者，等待確認後再繼續。
