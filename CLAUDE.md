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

## Agent skills

### Issue tracker

Issues 與 specs 放在 GitHub Issues（JLforAi/iflocus-website），以 `gh` CLI 操作。See `docs/agents/issue-tracker.md`.

### Domain docs

single-context（根目錄 `GLOSSARY.md` + `docs/adr/`，目前皆尚未建立）。See `docs/agents/domain.md`.

## 協作鐵則（每次 session 預設生效）

### 回覆與語言
- 一律以繁體中文回覆，含進度更新、錯誤訊息說明與完成回報。
- 每份指令開頭標明使用的模型與 effort；指令沒標時主動問。

### 分支與提交
- 永遠開 feature/ 或 fix/ 或 chore/ 前綴的分支，絕不直接 commit 或 push 到 main 或部署分支。
- 每個改動走 PR，PR 內文必須貼驗證指令的實際輸出，不可只寫「已驗證」。
- 不改寫歷史、不 force push。

### 視覺系統
- 未經明確同意，不動顏色、class、style、design tokens（locus-brand-tokens.css 及任何 data-brand 選擇器）。
- CSS 只能附加，不能修改或刪除既有規則。

### 動手前
- 大改動、刪檔、或不熟的區域，先做唯讀掃描並回報觀察，等指令再動手。
- 唯讀階段不做任何寫入或刪除，即使本檔其他規則有清理要求也一樣；要刪先停下來問。
- 改文案、改結構、改設定，先給 before/after，文字改動用 git diff --word-diff 驗證。
- 只做指令列的 Scope；Non-scope 的東西即使看到問題也只回報、不順手修。

### 碰到以下任一，停下來問，絕不自動執行
- 刪資料、刪目錄、批次改檔。
- 改 .github/workflows/、deploy 設定、CNAME、robots、sitemap，或任何其他部署相關檔。
- 動到 secrets、token、金鑰、密碼、付費或變現相關設定。
- 改 .gitignore、CLAUDE.md 既有內容。
- 超出本輪 Scope 的重構。

### 失敗與不確定
- 失敗、不確定、文件與程式對不上，直接講，以源碼為準，不粉飾、不硬補。

### 完成回報固定格式（每次任務結束都用這十項）
1. 處理了哪個任務
2. commit hash（完整）與 commit message
3. 是否已 push、PR 編號與連結
4. 修改了哪些檔（清單）
5. 改了什麼（摘要）
6. 用什麼指令驗證、實際輸出是什麼
7. 有沒有超出 Scope、有沒有碰到 Non-scope
8. 還有什麼沒做完
9. 有沒有需要本人確認的風險
10. 下一步建議

### 公司資訊
- 公司名稱用「Locus Marketing Technology」或「絡客思行銷科技」，對外文件負責人頭銜為執行長／CEO。

