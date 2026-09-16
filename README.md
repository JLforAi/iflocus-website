# iflocus-website

> 🎨 **前端開發前請先讀 [docs/BRAND-TOKENS.md](docs/BRAND-TOKENS.md)** — 品牌色 design tokens 規範（已上線，勿再寫死 hex 色碼）。

絡客思行銷科技（LOCUS）官方網站。靜態站，GitHub Pages 部署（自訂網域 [iflocus.com](https://iflocus.com)）。

## 開發者文件（`docs/`）

- [BRAND-TOKENS.md](docs/BRAND-TOKENS.md) — 品牌色 design tokens 開發須知（**必讀**）
- [CASE-PAGE-PLAYBOOK.md](docs/CASE-PAGE-PLAYBOOK.md) — case 頁製作指南
- [DEV_NOTES.md](docs/DEV_NOTES.md) — 開發筆記

## 結構速覽

- 頁面：根目錄 `*.html`；共用 nav/footer 由 `js/components.js` 注入
- 樣式：`css/locus-brand-tokens.css`（品牌色變數）＋ `css/style.css`（全站樣式）
- 品牌色：母站 LOCUS 藍為骨架，服務頁以 `<body data-brand="iflocus|ailocus|locusad">` 切換 accent（細節見 BRAND-TOKENS.md）
