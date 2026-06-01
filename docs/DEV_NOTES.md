# Dev notes — environment pitfalls

Running log of environment-level gotchas that have actually bitten us on this repo. Add new entries at the top; date them; keep the "spotted while" line so future-us can re-derive what triggered it.

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
