# 內容審查修正 SUMMARY

> Branch: `content-review-fixes`
> Date: 2026-05-06
> Total commits: 9

---

## ✅ 第一階段:純文字 / 排版修正(已完成)

| # | 項目 | Commit | 變更摘要 |
|---|---|---|---|
| 1 | 中英文間距(全站)| `17ef28f` | 18 個 live HTML(含 `internal/`)文字節點插入半形空格;`<style>`/`<script>`/attribute 不動 |
| 2 | 廣告用語合規 | `803c8c9` `144643f` | 14 處「業界最高」/「營收倍增」→「業界領先」/「實測」/「成長」 |
| 3 | about_us 連結 | — | 維持(略過)|
| 4 | 首頁聯播網標題 | `00cab1f` | 兩處「前 10 大 APP」→「主要合作 APP」 |
| 5 | locusad APP alt | `b2b898d` | 8 個 alt 對齊首頁名稱;image-9/10 標 `<!-- TODO -->` |
| 6 | branddrop 排版 | `54dadaf` | `How It Works` → `服務流程`;延伸服務區塊 `STEP 02-04` → `延伸服務`(去編號)|

---

## ✅ 第二階段:結構性修改(已完成)

| # | 項目 | Commit | 變更摘要 |
|---|---|---|---|
| 7 | iflocus.html 文字化 | `af79cce` | 8 張純圖頁 → 文字 + 配圖;新增 8 個 h2 章節與完整 h3 階層;原圖以 `<figure>` 保留作視覺輔助 |
| 8 | about_us 里程碑補洞 | `c44e1c4` | `2025` 圓圈 → `近年`;標題改為「持續發展與策略聯盟擴展」涵蓋 2022–2025 |
| 9 | case-studies 選戰連結 | `f613fb3` | `case-election.html` 加 `#strategy` `#community` `#sprint` 三個 anchor;首頁三個案例連結對應 hash |
| 10 | contact 隱私同意 | `c6b5854` | 表單加 required checkbox 連結 `privacy.html`;送出前 JS 雙重檢查 + 紅字錯誤訊息 |

---

## 📋 第三階段:需提供素材或決策的 TODO 清單(尚未動手)

### A. adlocus.com 圖片本地化(99 處,21 個檔案)

外部圖片 hotlink 仍然存在於以下 21 個檔案,共 **99 處**:

| 檔案 | 數量 |
|---|---|
| `case-studies.html` | 20 |
| `locusad.html` | 16 |
| `case-election.html` | 16 |
| `index.html` | 9 |
| `case-food.html` | 6 |
| `news.html` | 5 |
| `case-hk.html` | 4 |
| `locus_ps.html` | 3 |
| `ailocus.html` | 3 |
| `case-leisure.html` | 3 |
| `case-3c.html`, `case-product.html`, `case-omo.html` | 各 2 |
| `case-fashion.html`, `case-finance.html`, `case-telecom.html`, `case-realestate.html`, `case-event.html`, `case-survey.html`, `case-member.html`, `about_us.html` | 各 1 |

**待你確認**:
- [ ] 確認後我寫一個 Python 下載腳本,以 `curl -k` 把所有 `https://adlocus.com/wp-content/uploads/...` 下載到 `images/external/` 並更新 src 路徑
- [ ] 是否一併下載?或只下載特定檔案?(例:只先做 `index.html` + `case-studies.html`)
- [ ] 下載後是否要重新命名(例 `image-1.png` → `app-karaoke.png`)?

---

### B. 品牌定位統一(三處不一致)

iFLocus / AiLocus / 絡客思 描述出現於以下地方,**用語並未統一**,請逐一審視後提供統一論述:

1. **首頁 FAQ**(`index.html`)
   - 待確認:目前首頁是否仍有 FAQ?(現況已掃過,需你指認 FAQ 段落)
2. **about_us.html**
   - L40–60 左右的 mission / 公司介紹段落
   - 里程碑「創立」段落:「以行銷科技與整合服務起步,持續發展成以影響力營銷為主軸的跨域行銷夥伴」
3. **components.js HEADER/FOOTER**
   - Footer 描述:「以『場域行銷科技』為核心,結合大數據與 AI 運算,提供企業精準的場域行動廣告與整合行銷解決方案」

**待你確認**:
- [ ] 是否以「影響力營銷」為主軸?還是「場域行銷科技」?或「OMO 整合行銷」?
- [ ] AiLocus 的定位:大數據平台 / AI 工具 / 子品牌?
- [ ] 「絡客思」中文名稱出現位置是否需要與 iFLocus 並列?

確認後我會在這三處同步寫入統一論述。

---

### C. 案例授權確認(具名品牌清單)

`case-*.html` 共出現以下**具名品牌**,請逐一確認哪些有正式授權、哪些需改為去識別化:

#### 食品餐飲(`case-food.html`)
- 麥當勞、SUBWAY、漢堡王、統一純喫茶、勝博殿、饗泰多、香格里拉飯店餐廳、香帥蛋糕、健達巧克力

#### 休閒生活(`case-leisure.html`)
- 生活工場、HotelsCombined、麗星郵輪、W Hotel、Rivon 禮坊、健達繽紛樂

#### 女性時尚(`case-fashion.html`)
- 肌膚之鑰、AVON、Lancome、資生堂、花王 Sofina、ERNO LASZLO、Curel 珂潤、UNIQLO、Celio

#### 3C 科技(`case-3c.html`)
- Panasonic LUMIX、DELL、Bose、飛利浦、趨勢科技

#### 金融保險(`case-finance.html`)
- 聯邦銀行、花旗信用卡(寰旅世界卡)、星展銀行、永豐銀行、東亞銀行、澳盛銀行、康健人壽、新光人壽、施羅德基金、滙豐銀行

#### 電信通訊(`case-telecom.html`)
- 亞太電信、台灣之星、台灣大哥大(iPhone 7 推廣)、中華電信、遠傳電信

#### 房地產(`case-realestate.html`)
- 松漢掬雲

#### 產品推廣(`case-product.html`)
- 麥當勞 McCafe、康是美、聲寶百利市、聯合利華 Skip

#### 名單問卷(`case-survey.html`)
- 康軒文教

#### 虛實整合(`case-omo.html`)
- 東森 × 全家 TV Outlet

#### 香港地區(`case-hk.html`)
- Audi A3、nissen、中原電器 × 恆生信用卡、東亞銀行

**待你確認**:
- [ ] 在每個品牌後標 ✅(有授權)/ ❌(去識別化)/ ⚠️(改為通用描述如「某連鎖速食」)
- [ ] 確認後我批次替換所有具名品牌為對應處理方式

---

### D. 服務分類架構(三處不一致)

服務分類數量與名稱差異點:

#### 1. 首頁卡片區(`index.html` 服務卡片區)
- iFLocus OMO
- BrandDrop
- 場域手機推播廣告
- AiLocus

#### 2. 選單(`components.js` HEADER)
- iFLocus OMO
- BrandDrop(下拉:介紹 / 開始旅程)
- 場域手機推播廣告
- AiLocus
- LocusPS 企業版
- 加入 APP 聯播網

#### 3. 關於我們(`about_us.html`)
- 待掃描具體服務分類段落(尚未確認該頁是否有服務列表)

#### 4. Footer(`components.js` 產品服務 col)
- iFLocus OMO
- BrandDrop
- 場域手機推播廣告
- AiLocus
- LocusPS 企業版
- 加入 APP 聯播網

**主要不一致**:
- 首頁卡片只有 4 項,但選單/Footer 有 6 項
- `LocusPS 企業版`、`加入 APP 聯播網` 在首頁未呈現

**待你確認**:
- [ ] 統一為 4 項 / 6 項 / 其他結構?
- [ ] 是否新增首頁卡片補齊 LocusPS、APP 聯播網?
- [ ] 服務分類是否要分主類 / 子類(例:核心產品 / 周邊服務)?

---

## 📈 建議下一步

1. **先 push 現有分支**:`git push -u origin content-review-fixes` 後在 GitHub 開 PR 給你做整體 review
2. **等你回覆 A/B/C/D 的決策**後我再依序動手
3. 第一/二階段共 **9 個 commit** 都已分開,若任何一項要 revert 直接 `git revert <hash>` 即可
4. 第三階段預估完成後再做一次:
   - 圖片本地化導致的離線可運行性測試
   - 全站 broken link 掃描(特別是 `case-election.html` 三個 anchor 是否實際定位正確)
   - SEO 工具(Lighthouse / PageSpeed Insights)複測 `iflocus.html` 文字化後的分數
