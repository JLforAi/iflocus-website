# 品牌色 Design Tokens — 開發須知

> ✅ **已上線**：全站品牌色 design tokens（PR #15）＋ LOCUS CIS Book。
> 新增或修改頁面時，請遵循以下規範，**不要再寫死 hex 色碼**。

---

## 一句話心法

**骨架恆藍、服務色靠 `data-brand` 切換、accent 一律吃 `--brand-*`、絕不寫死 hex。**

- 母站 LOCUS 藍 `#0066CC` = 全站 UI 骨架（nav / footer / 共用連結），**不隨頁面變**。
- 各服務的識別色由 `<body data-brand="...">` 驅動，元件吃 `--brand-*` 就會自動換色。

---

## 新增 / 修改頁面 Checklist

1. **服務頁** → 在 `<body>` 掛對應 `data-brand`（見下表）。母站／共用頁不掛，自動沿用藍。
2. **accent 元素**（CTA、標題底線、icon、卡片邊框、強調字）→ 吃 `var(--brand-*)`。
3. **骨架元素**（nav / footer / 共用連結 / 麵包屑）→ 吃 `var(--locus-*)`，不要用 `--brand-*`。
4. **中性灰／黑白／邊框／陰影** → `var(--neutral-*)`。
5. **語意色** → 內容/數據強調紅用 `var(--emphasis)`；系統錯誤/失敗用 `var(--danger)`。
6. **任何顏色都不要寫死 hex**；需要新色先回到 tokens 檔定義。

## data-brand 對照

| data-brand | 服務 | 主色 |
|---|---|---|
| `iflocus` | 影響力營銷 | 金橘 `#EB9520` |
| `ailocus` | AI · 位置數據 | 紫 `#7E3D8E` |
| `locusad` | 場域推播 | 紅 `#D4252F` |
| （不掛） | 母站 / 共用頁 | LOCUS 藍 `#0066CC` |

> BrandDrop（`#FF4500` + 黑）自帶招牌色，**不納入此系統、勿改**。

---

## ⚠ 必記的一個陷阱：金橘按鈕

iFLocus 金橘 `#EB9520` 太亮，**配白字對比不及格**。實心金橘底的按鈕／色塊，文字必須吃 `var(--brand-on-fill)`（在 iFLocus 會自動解析成深棕 `#583608`）。**不要在金橘底上手動寫白字。**

---

## 別動這 7 類「刻意保留」的非 token 色

它們不是漏網的硬編碼，是有意義的顏色，**不要 token 化、不要洗成 accent**：

1. per-industry 主題色（case 頁的財經藍／休閒青綠／房產棕…）
2. 氛圍底色（米色 `#E8E0D0` 等暖色底）
3. case-election 的選情資料／分類色
4. internal 工具的 dark + gold 自帶設計系統
5. BrandDrop 招牌色 `#FF4500`
6. hero 區的裝飾洗色（低透明度 rgba）
7. 語意色三紅：`--brand-*`（品牌 accent）/ `--emphasis`（強調）/ `--danger`（錯誤）

---

## 反模式（別這樣做）

- ❌ 在已吃 `--brand-*` 的 class 上，又用 inline `style="background:#xxx"` 蓋回硬編碼 → 直接刪 inline，回歸 class。
- ❌ 把 nav / footer 染成服務色 → 骨架必須恆藍。
- ❌ 把主題色 / 資料色 / 子工具識別色洗成 accent → 主 accent 走 token，其餘保留。
- ❌ 服務頁掛了 `data-brand` 就把頁內每個有意義的識別色都改成該服務色 → 只換主 accent。

---

## 哪裡查

- **Tokens 檔**：`/css/locus-brand-tokens.css`（所有變數定義在此）
- **完整規範**：LOCUS CIS Book（PDF / HTML / PPTX）——品牌架構、色階、對比規則、用色治理
- **判斷顏色用途的尺**：頁面識別 → `--brand-*`；骨架 → `--locus-*`；中性 → `--neutral-*`；語意 → `--emphasis` / `--danger`；有意義的主題/資料/識別色 → 保留
