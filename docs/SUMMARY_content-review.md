# 內容審查修正 SUMMARY

> Branch: `content-review-fixes`
> Date: 2026-05-06
> Total commits: 14

---

## ✅ 第一階段:純文字 / 排版修正(已完成)

| # | 項目 | Commit | 變更摘要 |
|---|---|---|---|
| 1 | 中英文間距(全站)| `17ef28f` | 18 個 live HTML(含 `internal/`)文字節點插入半形空格;`<style>`/`<script>`/attribute 不動 |
| 2 | 廣告用語合規 | `803c8c9` `144643f` | 14 處「業界最高」/「營收倍增」→「業界領先」/「實測」/「成長」 |
| 3 | about_us 連結 | — | 維持(略過)|
| 4 | 首頁聯播網標題 | `00cab1f` | 兩處「前 10 大 APP」→「主要合作 APP」 |
| 5 | locusad APP alt | `b2b898d` | 8 個 alt 對齊首頁名稱;image-9/10 標 `<!-- TODO -->` |
| 6 | branddrop 排版 | `54dadaf` | `How It Works` → `服務流程`;延伸服務區塊 `STEP 02-04` → `延伸服務` |

---

## ✅ 第二階段:結構性修改(已完成)

| # | 項目 | Commit | 變更摘要 |
|---|---|---|---|
| 7 | iflocus.html 文字化 | `af79cce` | 8 張純圖頁 → 文字 + 配圖;新增 8 個 h2 章節與完整 h3 階層 |
| 8 | about_us 里程碑補洞 | `c44e1c4` | `2025` 圓圈 → `近年`;標題改為「持續發展與策略聯盟擴展」涵蓋 2022–2025 |
| 9 | case-studies 選戰連結 | `f613fb3` | `case-election.html` 加 `#strategy` `#community` `#sprint` 三個 anchor;首頁案例連結對應 |
| 10 | contact 隱私同意 | `c6b5854` | 表單加 required checkbox 連結 `privacy.html`;送出前 JS 雙重檢查 |

---

## ✅ 第三階段:策略性修正(已完成)

| # | 項目 | Commit | 變更摘要 |
|---|---|---|---|
| A | 圖片本地化 | `760a8c0` | 57 個 adlocus.com 圖檔下載至 `images/external/`;20 檔 111 處 src 改為本地路徑;共 11MB |
| B | 品牌定位統一 | `f7e2b60` | 確立「絡客思=公司,iFLocus/AiLocus=兩大主要服務」於 footer + about_us |
| C | 案例去識別化 | `c0741c0` | 全站 case-*.html 約 80 處具名品牌全部改為產業描述(麥當勞→國際速食連鎖品牌等)|
| D | 服務分類統一 | `8234106` | about_us 新增 `#services` 6 項分組(iFLocus 1 項 / AiLocus 3 項 / 獨立+合作 2 項);首頁加「查看全部服務」按鈕 |

---

## 🗂️ 服務分類最終架構

| 順序 | 名稱 | 連結 | 歸屬 |
|---|---|---|---|
| 1 | iFLocus OMO 整合行銷 | `iflocus.html` | **iFLocus** |
| 2 | BrandDrop AI 品牌頁面 | `branddrop.html` | **獨立服務** |
| 3 | 場域手機推播廣告 | `locusad.html` | **AiLocus** |
| 4 | AiLocus 位置大數據 | `ailocus.html` | **AiLocus** |
| 5 | LocusPS 企業版 | `locus_ps.html` | **AiLocus** |
| 6 | 加入 APP 聯播網 | `app_partners.html` | **合作夥伴計畫** |

---

## ⚠️ 殘留 TODO(技術 / 後續)

- [ ] **locusad image-9 / image-10 APP 名稱**:目前 alt 標 `合作 APP`(HTML 註解標 TODO),等補上 2 個 APP 的圖片與名稱
- [ ] **iFLocus-網頁-v3-* 中文檔名**:GitHub Pages 應該 OK,但若部署到其他 server 可能需 URL-encode 路徑
- [ ] **2022 / 2023 / 2024 里程碑**:目前統合為「近年」,若內部有具體事件可再分年細化
- [ ] **首頁 OG 圖**:`https://iflocus.com/images/og-image.jpg` 尚未確認檔案存在(多頁 meta 引用)
- [ ] **GA Measurement ID**:全站仍是 `GA_MEASUREMENT_ID` 占位字串,需替換為實際 GA4 ID
- [ ] **服務內頁的歸屬說明**:`locusad.html` / `ailocus.html` / `locus_ps.html` 的 hero 是否要明示「AiLocus 服務」標籤(目前只在 about_us 與首頁 card 內提及)

---

## 📈 建議下一步

1. **本機測試** — 開 `index.html` 測試 8 大頁面在新分類下的點擊路徑與 anchor 跳轉
2. **Push** — `git push -u origin content-review-fixes` 後在 GitHub 開 PR 做整體 diff review
3. **PageSpeed / Lighthouse** — 圖片本地化後預期 LCP 提升;`iflocus.html` 文字化後預期 SEO 分數提升
4. **若任何項目要 revert**:每項都是獨立 commit,直接 `git revert <hash>` 即可

---

## 📜 完整 Commit 歷程

```
8234106 fix(content): [D] 服務分類統一
c0741c0 fix(content): [C] 案例授權 - 具名品牌去識別化
f7e2b60 fix(content): [B] 品牌定位統一
760a8c0 feat(content): [A] 圖片本地化
ac49289 docs: SUMMARY 階段性
af79cce fix(content): [7] iflocus.html 文字化
c6b5854 fix(content): [10] contact 隱私 checkbox
f613fb3 fix(content): [9] case-election anchor
c44e1c4 fix(content): [8] about_us 里程碑「近年」
54dadaf fix(content): [6] branddrop 排版
b2b898d fix(content): [5] locusad APP alt
00cab1f fix(content): [4] 主要合作 APP
144643f fix(content): [2b] meta 補修
803c8c9 fix(content): [2] 廣告用語合規
17ef28f fix(content): [1] 中英文間距
```
