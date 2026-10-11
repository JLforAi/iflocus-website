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

## 行為規則（Karpathy guidelines，來源 forrestchang/andrej-karpathy-skills）

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
