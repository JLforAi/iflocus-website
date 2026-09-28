# Dev notes — environment pitfalls

Running log of environment-level gotchas that have actually bitten us on this repo. Add new entries at the top; date them; keep the "spotted while" line so future-us can re-derive what triggered it.

---

## iOS Chrome tap event 吞噬陷阱

**問題**:CTA 卡在 iPhone Safari 可點,但 iPhone Chrome 無反應。長按可跳出標準 link context menu(URL 顯示正常)→ 證明 `<a>` 結構、href、touch 抵達 anchor 的路徑全部沒問題,**只有「短促 tap → click event」這條路被吞**。

**根本原因(雙因子,iOS Chrome 兩個都踩,Safari 只踩一個還容錯):**

- **B. transition 在 tap 瞬間吞 click**
  元素自帶 `transition` 屬性時,iOS Chrome 對 click event 的 state machine 處理比 Safari 嚴格。在某些 paint frame 上,tap 落在「正準備 transition」的元素 → Chrome 視為「正在動畫中、忽略 click」。Safari 容錯。
- **C. SVG icon 觸發 gesture 歧義消除**
  `<a>` 內含 SVG icon 子元素。iOS Chrome 對 tap 落點是 SVG 的情況會進入額外手勢識別階段(候選包含「圖片預覽」),歧義消除期間 short tap 的 click 被「等等再決定」然後丟棄。Safari 走更直接的 hit-test path。

**修復:三道防線(僅動 css/style.css,HTML 完全不動)**

1. **`touch-action: manipulation`** — 取消 300ms 雙擊延遲與 hover 合成
2. **子元素全部 `pointer-events: none` + `<a>` 自己 auto** — 強制 click target 一定是 anchor,SVG 完全不參與 hit-test
3. **`@media (hover: hover) and (pointer: fine)`** 雙重 gating,**transition 與 hover 規則都搬進去** — 觸控裝置上元素根本沒 transition,B 因子無從觸發

**診斷依據**:長按 context menu 完全正常 + Safari/Chrome 差異 + 社群 issue 紀錄推導。**無 BrowserStack / SauceLabs,真機 ground truth 仍要靠 Joseph iPhone Chrome 實測**。

**末選方案(若 CSS 三道防線仍失敗)**:
JS `onclick` handler 強制 `window.open(href, '_blank')`。SEO / a11y 較差,所以是 fallback。

- **Spotted**: 2026-06-01, `fix/ios-chrome-tap` branch
- **Spotted while**: 7/1 對外發布前最終真機驗收;PR #3 的 `(hover: hover)` gate 在 Safari 過、Chrome 仍失敗

### 結局更新(2026-06-01,PR #5)

CSS 三道防線 deploy 後 Joseph iPhone Chrome 真機測試 **仍失敗**。Safari + Android + 桌機都正常,只有 iOS Chrome 吞 click。

最終啟動末選方案:**JS `touchend` handler 補觸發 `window.open`**(`js/cta-tap-fallback.js`)。CSS 防線**保留**作為其他瀏覽器的第一層,iOS Chrome 走 JS 補洞。

**行為流程:**
1. CSS 防線正常的瀏覽器 → tap → `<a>` click event → 跳轉(JS handler 看到 `alreadyHandled === false`,讓 click 跑)
2. iOS Chrome 吞 click → 沒有 click 派發 → JS `touchend` handler 判定 duration < 500ms + delta < 10px → 自己呼叫 `window.open(href, target)`
3. 防雙跳轉:`alreadyHandled` flag + `e.preventDefault()` in both touchend and click handlers

**代價:** SEO / a11y 略差(JS 觸發跳轉非語意化),但因 `<a href>` 仍存在,搜尋引擎與螢幕閱讀器仍能正確識別連結。

**Scope:** Script 只 attach 到 `a.fb-video-cta-card`,footer / nav 等其他 link **完全不碰**。

**教訓:** 未來如新做可點卡片元素,直接走 JS `touchend` 兜底較省事,不要依賴 CSS-only 修法處理 iOS Chrome 的事件吞噬問題。改一條 attribute / 一條 CSS 都可能讓 hit-test 進入新的歧義消除分支。

**Spotted while (PR #5):** PR #4 deploy 完成後 Joseph 真機 ground truth 驗收,Chrome 仍 dead。

### 🎯 真相揭曉與結案(2026-06-01)

經 Joseph 用「**有 FB App 的同事手機**」對照測試,確認真正原因:

**iOS Chrome 對 `facebook.com` 跨域跳轉的協定攔截:**
- 用戶有 FB App → iOS Chrome 喚起 App ✅
- 用戶沒有 FB App → 無 fallback,呈現「無反應」❌
- iOS Safari → 系統預設瀏覽器有特殊權限,fallback 到網頁 ✅

**原診斷(click event 吞噬、hover quirk、transition state machine、SVG hit-test 歧義)方向皆錯**。PR #3 / #4 / #5 的修法未解原問題。

**影響範圍:** 全站訪客 < 1%(iOS Chrome 且未裝 FB App 的交集)。此族群仍可長按複製連結、或切 Safari 開啟。

**結案決議:不 revert 任何 PR**,理由:

1. **SEO/a11y 實質影響為 0**
   - `<a href>` 標籤完整保留,搜尋引擎正常識別
   - 螢幕閱讀器走 click 路徑,JS 不干擾
   - 鍵盤 Tab + Enter 操作不受影響

2. **帶來實質改善**
   - CTA 卡視覺差異化(產品需求)
   - `touch-action: manipulation` 提升一般觸控反應
   - 其他瀏覽器 click event 異常 case 仍有保護

3. **完整除錯歷程作為工程資產**

**教訓:**

- Web bug 真機驗證務必涵蓋「最小可重現環境」,包括「**沒裝相關 App**」這種看似不重要的條件
- Chrome DevTools 模擬與單一真機都無法覆蓋「**App 喚起**」這類 OS 層級交互行為
- 跨 App 跳轉(`facebook://`、`line://`、`whatsapp://` 等)未來實作時應**先評估「沒裝對應 App 的 fallback 行為」**

---

## Git Bash on Windows 中文路徑陷阱

直接傳中文路徑作為 git 引號參數會 silent fail:

```
❌ git add "images/external/2017/07/資策會_智慧城市展_xxx.jpg"
   (無錯誤訊息、無效果,但 git status 仍顯示 untracked)
```

正確做法:

```
✅ git add images/external/2017/07/         # 目錄層
✅ git add -A images/external/2017/07/      # pathspec
```

影響範圍:任何含中文檔名的 git 操作。Script 化時務必避免直接傳中文路徑參數,改用目錄或 pathspec。

- **Spotted**: 2026-06-01, `feature/fb-integration` branch
- **Spotted while**: 處理 `images/external/` untracked 圖檔時遇到
