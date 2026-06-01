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
