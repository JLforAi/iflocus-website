# Case Page Migration Playbook
**目的**：把 `case-XXX.html`（XXX = 產業）從 adlocus.com 的對應分類完整搬過來，一次成功，含 iOS/Android/Diamond tab 切換、點擊後活動頁 crossfade、手指點擊動畫、品牌資料、圖片審核。

> 這份文件是 3C 案例（case-3c.html）走過 6 輪迭代後沉澱出的「正確流程」。下次遷移其他產業時照做即可避免重踩坑。

---

## ⚡ 觸發指令（給未來的 Claude Code 用）

把下面這段貼到 Claude Code，把 `{INDUSTRY}` / `{ADLOCUS_CAT_SLUG}` / `{CAT_ID}` 換成目標分類即可：

```
請依 CASE-PAGE-PLAYBOOK.md 的完整流程，把 case-{INDUSTRY}.html 從
https://adlocus.com/case-studies/{ADLOCUS_CAT_SLUG}/ (cat_id={CAT_ID})
完整遷移過來。要求：

1. 用 WP REST API 抓該分類所有文章 + 每篇的隱藏「活動頁」attachment
2. 下載所有推播圖 + 點擊後活動頁圖到 images/external/YYYY/MM/
3. 寫成 tab + crossfade 結構（.case-mockup-tabbed 模板，CSS/JS 已在 style.css + main.js）
4. 完成後跑圖片審核（每張 > 1KB 且視覺對題）
5. bump cache-bust query string、commit、push
6. 遵守用詞規則（不出現 AdLocus / 業界最高 / 營收倍增 等禁用詞）

完成後給我變更摘要。
```

**已知分類對照表**（adlocus.com WP REST `/wp-json/wp/v2/categories`）：

| 產業 | iflocus 檔名 | adlocus slug | cat_id | 文章數 |
|------|------------|------------|--------|------|
| 3C 科技 | case-3c.html | consumerelectronics | 40 | 7 ✅ 已完成 |
| 食品餐飲 | case-food.html | food | 37 | 20 |
| 女性時尚 | case-fashion.html | female-fashion | 35 | 11 |
| 休閒生活 | case-leisure.html | leisure | 36 | 19 |
| 金融保險 | case-finance.html | financia-insurance | 38 | 10 |
| 電信通訊 | case-telecom.html | telecommunications | 39 | 5 |
| 房地產 | case-realestate.html | property | 68 | 1 |
| 香港地區 | case-hk.html | hong-kong | 49 | 9 |
| 會員推廣 | case-member.html | customers-promotion | 42 | 8 |
| 名單問卷 | case-survey.html | customerlist-questionnaire | 46 | 7 |
| 產品推廣 | case-product.html | products-promotion | 41 | 43 |
| 優惠活動 | case-promo.html | promotional-event | 43 | 28 |
| 實體活動 | case-event.html | events | 44 | 22 |
| 虛實整合 | case-omo.html | online2offline | 45 | 15 |
| 案例報告 | case-report.html | report | 112 | 1 |
| 智慧選戰 | case-election.html | (無) | — | — |

---

## 📋 8 步遷移流程

### Step 1：抓分類所有文章
```bash
CAT_ID=40   # 例：3C
curl -sL --ssl-no-revoke \
  "https://adlocus.com/wp-json/wp/v2/posts?categories=${CAT_ID}&per_page=50&_fields=id,title,slug,link" \
  -o ~/stash/posts.json
PYTHONIOENCODING=utf-8 python3 -c "
import json,os,sys
sys.stdout.reconfigure(encoding='utf-8')
for p in json.load(open(os.path.expanduser('~/stash/posts.json'),encoding='utf-8')):
    print(f\"id={p['id']:5} {p['title']['rendered']}  link={p['link']}\")"
```

### Step 2：抓每篇案例頁的 tab 結構 + finger 變體
```bash
# 把每個 slug 的頁面存下來
for slug in slug-a slug-b slug-c ; do
  curl -sL --ssl-no-revoke "https://adlocus.com/${slug}/" -o ~/stash/${slug}.html
done

PYTHONIOENCODING=utf-8 python3 << 'PY'
import re, os, sys
sys.stdout.reconfigure(encoding='utf-8')
SLUGS = ['slug-a', 'slug-b', 'slug-c']
for slug in SLUGS:
    html = open(os.path.expanduser(f'~/stash/{slug}.html'), encoding='utf-8', errors='replace').read()
    print(f"\n=== {slug} ===")
    labels = re.findall(r'href=[^>]*?#(tab-[0-9-]+)[^>]*>([^<]+)<', html)
    label_by_id = {tid: lbl for tid, lbl in labels}
    panels = re.split(r'id=(tab-[0-9-]+)\s+class="wpb_tab', html)
    for i in range(1, len(panels), 2):
        tid = panels[i]
        body = panels[i+1][:8000] if i+1 < len(panels) else ''
        fingers = re.findall(r'finger finger(\d+)', body)
        imgs = re.findall(r'src=(https?://adlocus\.com/wp-content/uploads/[^\s>"]+\.\w+)', body)
        lbl = label_by_id.get(tid, '?')
        # 前 1 張圖通常是該 tab 的推播畫面
        print(f"    [{lbl}] finger={fingers[0] if fingers else '?'}  notify_img={imgs[0].split('/')[-1] if imgs else '?'}")
PY
```

### Step 3：抓「點擊後活動頁」隱藏附件（**關鍵踩坑點**）
**⚠️ 重要：AdLocus 把活動頁圖綁在 WP attachment 但不在 HTML 引用，靜態解析會漏掉。**

```bash
mkdir -p ~/stash/attachments
for post_id in 2271 2325 2396 ; do
  curl -sL --ssl-no-revoke \
    "https://adlocus.com/wp-json/wp/v2/media?parent=${post_id}&per_page=50&_fields=id,title,source_url" \
    -o ~/stash/attachments/${post_id}.json
done

PYTHONIOENCODING=utf-8 python3 << 'PY'
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
POSTS = {2271:'Panasonic', 2325:'聲寶'}
for pid, name in POSTS.items():
    data = json.load(open(os.path.expanduser(f'~/stash/attachments/{pid}.json'), encoding='utf-8'))
    print(f"\n=== [{pid}] {name} — {len(data)} attachments ===")
    for m in data:
        title = m['title']['rendered']
        url = m['source_url']
        is_landing = '活動頁' in title or '详情' in title or '活动' in title
        marker = '🎯' if is_landing else '  '
        print(f"  {marker} id={m['id']:5} title={title!r}")
        print(f"            url={url}")
PY
```

`parent=None` 的 attachment（如聲寶 Diamond-PUSH.jpg）要全域搜尋：
```bash
curl -sL "...wp-json/wp/v2/media?search=Diamond-PUSH&per_page=20&_fields=id,title,source_url,post"
```

### Step 4：下載所有圖片
```bash
DEST="/g/我的雲端硬碟/iflocus-website/images/external/2017/07"  # 用 Unix path！
mkdir -p "$DEST"

# 普通檔名
curl -sL --ssl-no-revoke "URL" -o "$DEST/filename.jpg"

# CJK 檔名要 URL-encode（中文字元用 %XX%XX%XX）
# 例：活動頁.jpg → %E6%B4%BB%E5%8B%95%E9%A0%81.jpg
curl -sL --ssl-no-revoke \
  "https://adlocus.com/wp-content/uploads/2017/08/KC_HK_%E4%B8%AD%E5%8E%9F%E9%9B%BB%E5%99%A8_%E6%B4%BB%E5%8B%95%E9%A0%81.jpg" \
  -o "$DEST/KC_HK_中原電器_活動頁.jpg"
```

**並行下載多張**：用 `&` 背景化 + `wait`，明顯加速。

```bash
curl -sL ... &
curl -sL ... &
curl -sL ... &
wait
```

### Step 5：視覺驗證每張圖
**必做**。用 Read tool 打開每張新下載的圖確認內容對題。AdLocus 的「活動頁」應該是手機瀏覽器顯示品牌官網/著陸頁。常見錯認：
- ❌ 把 banner 廣告當活動頁
- ❌ 把產品照當推播畫面
- ✅ 推播畫面：手機鎖屏 / 通知欄
- ✅ 活動頁：手機瀏覽器 URL bar + 品牌官網內容

```bash
# 在 Claude 對話內：用 Read 工具打開每張圖
# Read("G:\\我的雲端硬碟\\iflocus-website\\images\\external\\2017\\07\\Panasonic_活動頁.jpg")
```

### Step 6：寫 HTML — Tab + Crossfade 模板

**模板**（每個案例的 image block 用這個結構）：

```html
<div class="case-mockup-tabbed">
  <div class="mockup-tab-nav">
    <button type="button" class="mockup-tab active" data-tab="ios">iOS</button>
    <button type="button" class="mockup-tab" data-tab="android">Android</button>
    <!-- 視該案例 AdLocus 原版 tab 數調整：可能 1-3 個 -->
  </div>
  <div class="mockup-panels">
    <div class="mockup-panel active" data-tab="ios">
      <div class="case-push-block">
        <!-- 底層：點擊後活動頁（永遠可見） -->
        <img class="screen-after" loading="lazy"
             src="images/external/YYYY/MM/品牌_活動頁.jpg"
             alt="品牌 活動頁（iOS 點擊後）" onerror="this.style.display='none'">
        <!-- 上層：推播畫面（會淡出露出底層） -->
        <img class="screen-before" loading="lazy"
             src="images/external/YYYY/MM/品牌_iOS.jpg"
             alt="品牌 iOS 推播畫面" onerror="this.style.display='none'">
        <!-- 手指點擊動畫 -->
        <div class="finger-code"><div class="finger fingerN"></div></div>
      </div>
    </div>
    <div class="mockup-panel" data-tab="android">
      <!-- 同上，換 Android 圖 + 對應 finger 變體 -->
    </div>
  </div>
</div>
```

**規則**：
- `screen-after` 是底層（活動頁），永遠可見
- `screen-before` 是上層（推播畫面），會 4s 淡出露出底層
- `fingerN`（N=1-6）對應 AdLocus 原版使用的變體
- 沒有「點擊後活動頁」的案例（如 3C 的聲寶）只放 `screen-before`、省略 `screen-after`
- iOS/Android/Diamond tab 數量比照 AdLocus 原版

### Step 7：圖片審核（**必做**）
```bash
cd "/g/我的雲端硬碟/iflocus-website"
IMGS=(
  "images/external/2017/07/Panasonic_iOS.jpg"
  "images/external/2017/07/Panasonic_活動頁.jpg"
  # ... 列出所有新增圖
)
for img in "${IMGS[@]}"; do
  if [ -f "$img" ]; then
    size=$(stat -c%s "$img" 2>/dev/null)
    [ "$size" -gt 1000 ] && echo "✅ $img ($((size/1024))K)" || echo "❌ TOO SMALL $img"
  else
    echo "❌ MISSING $img"
  fi
done
```

### Step 8：Cache-bust + Commit + Push
- 在 case-XXX.html 的 `<link rel="stylesheet" href="css/style.css?v=YYYYMMDD-XXX">` 升版號
- Commit 訊息描述變更（用過去的 commit 為參考）
- `git push`，等 GitHub Pages 部署（1-3 分鐘）

---

## 🛠️ CSS / JS 依賴（已在專案內，不需要重寫）

| 元件 | 位置 |
|------|------|
| `.case-mockup-tabbed` / `.mockup-tab` / `.mockup-panel` widget | `css/style.css` ~line 1320 |
| `.case-push-block` / `.screen-before` / `.screen-after` 疊層 + crossfade | `css/style.css` ~line 1300 |
| `.finger-code` / `.finger1`–`.finger6` 點擊動畫 | `css/style.css` ~line 1320 |
| `pushFadout` + `fingerTap1`–`6` keyframes | `css/style.css` ~line 1340 |
| tab 切換 JS handler | `js/main.js` ~line 180 |

新案例頁只要 `<link rel="stylesheet" href="css/style.css?v=...">` + `<script src="js/main.js"></script>` 就能用。

---

## 🎯 Finger 變體對照表

從 AdLocus CSS 的 `@keyframes fingerTap*` 提取，挑「最接近推播訊息垂直位置」的變體：

| variant | tap 位置 (top%) | 推播畫面適用 |
|---------|----------------|------------|
| finger1 | 7%  | iOS 鎖屏最頂端 / Android 通知第一則 |
| finger2 | 15% | iOS / Android 通知上方 |
| finger3 | 38% | 中上 / Diamond PUSH 上半 |
| finger4 | 32% | Android 通知欄中間 |
| finger5 | 46% | 中下 / 大版面廣告中段 |
| finger6 | 26% | 大版面 banner / Bose 類整版廣告 |

不確定時直接看 AdLocus 原版 HTML 用哪個（步驟 2 已抓出）。

---

## 🚧 已知踩坑點（避免重蹈覆轍）

| 坑 | 解法 |
|----|------|
| `/tmp/` 在 Windows shell 不持久 | 用 `~/stash/`（自己 mkdir）|
| Python `os.path` 處理 CJK 路徑會 UnicodeError | `PYTHONIOENCODING=utf-8` + `sys.stdout.reconfigure(encoding='utf-8')` |
| curl 在 Windows 卡 SSL 撤銷檢查 | 加 `--ssl-no-revoke` |
| Bash `ls` 顯示 CJK 變亂碼但檔案實際 OK | 用 `find` 或 Glob tool 替代 |
| CJK 檔名 URL 要先 url-encode 才能 curl | 用 `python3 -c "import urllib.parse;print(urllib.parse.quote('活動頁'))"` |
| AdLocus 圖淡出露白底很醜 | **必須**用 `.screen-after` 疊底層活動頁 |
| `prefers-reduced-motion` safeguard 會關掉動畫 | 不要加，會被 OS 設定誤殺 |
| Style.css 有 cache → 改了沒反應 | bump `?v=YYYYMMDD-xxx` query string |
| `data-dt-location` attachment URL 直接回傳圖 | 不是 HTML 頁，不需另外解析 |
| WP REST `parent=POST_ID` 漏掉某些 attachment | 用 `search=keyword` 全域搜（如聲寶 Diamond-PUSH parent=None）|
| 頁面 HTML 裡的 `<img src>` 可能包含無關圖片（別的廣告、模板裝飾圖等） | **必須以 `wp/v2/media?parent=POST_ID` 的 attachment 清單為準**，不要直接抓頁面 HTML 裡的圖 URL；attachment id 才是確認歸屬的唯一依據 |
| `display: inline-block` 在 grid 內可能不撐滿 | 加 `width: 100%` 補回 |

---

## ✍️ 用詞規則（**強制遵守**）

- 公司：**絡客思行銷科技** / Locus Marketing Technology CO., LTD.
- 服務：**iFLocus** / **AiLocus**（**不是**公司名，別寫「iFLocus 絡客思行銷科技」）
- **禁止出現** `AdLocus` 字樣（前台任何位置；URL 例外：`ps.adlocus.com`）
- **禁用浮誇詞**：業界最高 / 營收倍增 / 業界最佳表現 → 改寫 業界領先 / 實測 / 成長
- 中文標點全形：，。；：！？
- 不主動加 emoji（除非用戶要求）

---

## 🔎 在地 Preview

```bash
# Project 根目錄已設定好 .claude/launch.json (port 8765)
# Claude Preview 直接呼叫 mcp__Claude_Preview__preview_start name="iflocus-preview"
```

開瀏覽器後可用 `preview_inspect` / `preview_screenshot` 驗證動畫。

---

## 🎬 一行驗收檢查

部署後請：
1. 強制重整 https://iflocus.com/case-XXX.html （Ctrl+Shift+R）
2. 切換 tab（iOS / Android / Diamond）→ 推播畫面應換成該平台版本
3. 觀察 4 秒：手指圓圈從右側滑入點擊 → 推播淡出 → 底層活動頁露出
4. 案例分類頁（case-studies.html）對應卡片描述要更新成「跨平台/跨品牌」標題

---

## ✅ 完工自我檢查清單（commit 前必跑）

```bash
cd "/g/我的雲端硬碟/iflocus-website"
PAGE=case-XXX.html

echo "--- 1. 禁用詞 ---"
grep -iE "AdLocus|業界最高|營收倍增|業界最佳表現" "$PAGE" || echo "(clean)"

echo "--- 2. 所有 src 路徑皆在 git ---"
grep -oP 'src="images/external/[^"]*"' "$PAGE" | sed 's/src="//;s/"//' | sort -u | while IFS= read -r p; do
  [ -z "$(git ls-files "$p")" ] && echo "NOT-IN-GIT: $p"
done && echo "(done)"

echo "--- 3. 各圖片確實存在且 >1KB ---"
grep -oP 'src="images/external/[^"]*"' "$PAGE" | sed 's/src="//;s/"//' | sort -u | while IFS= read -r p; do
  [ ! -f "$p" ] && echo "MISSING: $p" && continue
  sz=$(stat -c%s "$p" 2>/dev/null)
  [ "$sz" -lt 1024 ] && echo "TOO_SMALL($sz): $p"
done && echo "(done)"

echo "--- 4. screen-before / screen-after 計數 ---"
sb=$(grep -c "screen-before" "$PAGE")
sa=$(grep -c "screen-after"  "$PAGE")
echo "  screen-before=$sb  screen-after=$sa  push-only=$(( sb - sa ))"
echo "  若 push-only > 0，必須有 :not(:has(.screen-after)) animation:none 規則"
grep ":has(.screen-after)" "$PAGE" && echo "  (rule found)" || echo "  ⚠ MISSING :has() rule"

echo "--- 5. 檔名大小寫衝突（同目錄相同名稱只差大小寫） ---"
grep -oP 'images/external/[^"]+' "$PAGE" | sort -u | awk -F'/' '{print tolower($0)" "$0}' | sort | awk 'prev==$1{print "COLLISION: "$2} {prev=$1}' || echo "(none)"

echo "--- 6. main.js 已引入 ---"
grep -c "js/main.js" "$PAGE" | grep -q "^[1-9]" && echo "  (found)" || echo "  ⚠ MISSING <script src=js/main.js>"

echo "--- 7. cache-bust query string 含產業碼 ---"
grep "style.css?v=" "$PAGE" || echo "  ⚠ MISSING cache-bust"
```

**檢查項目說明**：

| # | 檢查內容 | 若失敗怎麼辦 |
|---|---------|------------|
| 1 | 無禁用詞 | 全文搜尋替換 |
| 2 | 所有圖路徑在 git index | `git add` 補上，或修正路徑 |
| 3 | 圖存在且 >1KB | 重新 curl 下載；1KB 以下是伺服器 404 頁 |
| 4 | push-only panel 有 animation:none | 在頁內 `<style>` 加 `:not(:has(.screen-after)) .screen-before { animation: none; }` |
| 5 | 無大小寫衝突（Windows 不分大小寫，但 GitHub Pages Linux 區分）| 給衝突的其中一方重新命名（加品牌前綴，如 `kapiti-500x888.jpg`），更新 HTML，重新下載 |
| 6 | main.js 已引入 | 在 `</body>` 前加 `<script src="js/main.js"></script>` |
| 7 | cache-bust 有更新 | 改成 `?v=YYYYMMDD-XXX` |

> 📌 **大小寫衝突的根本預防**：同一目錄若有多篇案例使用泛型活動頁名（`500x888.jpg`、`500X888.jpg`），下載時一律改以品牌前綴命名（`kapiti-500x888.jpg`、`duanchunzhen-500x888.jpg`），完全避免衝突。

---

_文件版本：v1.1（2026-05-26）— 新增自我檢查清單，來自食品餐飲案例遷移後沉澱_
