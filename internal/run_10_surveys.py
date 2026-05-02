"""
SurveyAI — 10 份問卷自動填寫模擬
執行：python -X utf8 run_10_surveys.py
選項：
  --headless          無頭模式（不顯示瀏覽器視窗）
  --proxy-list FILE   每行一個 http://ip:port，輪流使用
  --form-url URL      指定真實 Google Form / SurveyCake URL
  --count N           份數（預設 10）
"""

import sys, io, time, csv, random, argparse, json
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent

# ── 顏色輸出 ────────────────────────────────────────────────────
G = "\033[92m"; Y = "\033[93m"; B = "\033[94m"; R = "\033[91m"; X = "\033[0m"
def log(msg, c=B):  print(f"{c}{msg}{X}", flush=True)
def ok(msg):        print(f"{G}  ✓ {msg}{X}", flush=True)
def warn(msg):      print(f"{Y}  ⚠ {msg}{X}", flush=True)
def err(msg):       print(f"{R}  ✗ {msg}{X}", flush=True)

# ════════════════════════════════════════════════════════════════
# 10 位受訪者 Persona
# ════════════════════════════════════════════════════════════════
PERSONAS = [
    {
        "name": "林雅婷", "gender": "female", "age": "25-34",
        "occupation": "行銷企劃", "income": "45k",
        "personality": "品牌忠誠型，重視成分標示",
        "platform": "Instagram 和品牌官網",
        "reason": "我最重視成分安全性，特別是無防腐劑、無香精的產品。有機認證對我來說是重要的信任指標。",
        "age_val": "25-34", "products": [0, 1, 2],
        "budget": "1000–2000", "organic_score": 5,
    },
    {
        "name": "陳建宏", "gender": "male", "age": "35-44",
        "occupation": "軟體工程師", "income": "70k",
        "personality": "理性分析型，比較 CP 值",
        "platform": "Momo、PTT 開箱文",
        "reason": "主要看評價數量和成分表，價格合理最重要。有機認證加分但不是必要條件。",
        "age_val": "35-44", "products": [0, 3],
        "budget": "500–1,000", "organic_score": 3,
    },
    {
        "name": "黃美玲", "gender": "female", "age": "45-54",
        "occupation": "家庭主婦", "income": "30k",
        "personality": "謹慎保守型，口耳相傳",
        "platform": "朋友推薦和藥妝店",
        "reason": "朋友介紹的才用，用習慣就不換了。價格實惠最重要，不太懂成分。",
        "age_val": "45-54", "products": [0, 4],
        "budget": "500以下", "organic_score": 2,
    },
    {
        "name": "張怡君", "gender": "female", "age": "25-34",
        "occupation": "護理師", "income": "55k",
        "personality": "健康意識強，願意溢價",
        "platform": "YouTube 美妝頻道",
        "reason": "工作關係很重視皮膚健康，有機成分讓我比較放心。寧可多花一點錢買安心。",
        "age_val": "25-34", "products": [0, 1, 2, 3],
        "budget": "1000–2000", "organic_score": 5,
    },
    {
        "name": "王志偉", "gender": "male", "age": "18-24",
        "occupation": "大學生", "income": "15k",
        "personality": "衝動消費型，追流行",
        "platform": "TikTok 和蝦皮",
        "reason": "看到網紅推就買，主要看外包裝好不好看，價格不能太貴。",
        "age_val": "18-24", "products": [3],
        "budget": "500以下", "organic_score": 1,
    },
    {
        "name": "蔡佳穎", "gender": "female", "age": "35-44",
        "occupation": "自由業設計師", "income": "60k",
        "personality": "環保意識強，注重永續",
        "platform": "小紅書和品牌官網",
        "reason": "環境永續很重要，有機認證代表對環境友善。願意支付合理溢價。",
        "age_val": "35-44", "products": [0, 1, 2, 4],
        "budget": "2,000以上", "organic_score": 5,
    },
    {
        "name": "李明哲", "gender": "male", "age": "45-54",
        "occupation": "業務主管", "income": "90k",
        "personality": "品質導向，不在乎價格",
        "platform": "百貨公司專櫃",
        "reason": "品牌口碑和實際效果最重要，有機認證是加分項目。不會為了省錢買來路不明的產品。",
        "age_val": "45-54", "products": [0, 1],
        "budget": "2,000以上", "organic_score": 4,
    },
    {
        "name": "吳欣怡", "gender": "female", "age": "18-24",
        "occupation": "社群媒體工作者", "income": "35k",
        "personality": "潮流敏感，重視包裝質感",
        "platform": "Instagram 和 PChome",
        "reason": "包裝質感很重要，要適合拍照打卡。有機標章讓貼文看起來更有質感。",
        "age_val": "18-24", "products": [0, 2, 3],
        "budget": "500–1,000", "organic_score": 3,
    },
    {
        "name": "鄭雅文", "gender": "female", "age": "25-34",
        "occupation": "教師", "income": "50k",
        "personality": "研究型購物，看成分表",
        "platform": "美妝板和品牌官網",
        "reason": "買之前會詳細研究成分，特別在意致痘成分和防腐劑。有機認證可以節省我的研究時間。",
        "age_val": "25-34", "products": [0, 1, 2, 4],
        "budget": "1000–2000", "organic_score": 4,
    },
    {
        "name": "許家豪", "gender": "male", "age": "35-44",
        "occupation": "創業者", "income": "80k",
        "personality": "效率導向，重視效果",
        "platform": "電商評論和朋友推薦",
        "reason": "時間有限，直接看效果評價。有機不有機不重要，有效才重要。",
        "age_val": "35-44", "products": [0, 3],
        "budget": "500–1,000", "organic_score": 2,
    },
]

# ── UA 池（真實 Chrome UA，含 Mac / Windows / Android）────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080}, {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},  {"width": 1280, "height": 800},
    {"width": 390,  "height": 844},  {"width": 414,  "height": 896},
]

# 答案對應表（對應 mock_google_form.html）
AGE_MAP = {
    "18-24": 0, "25-34": 1, "35-44": 2, "45-54": 3, "55+": 4
}
BUDGET_LABELS = ["500以下", "500–1,000", "1000–2000", "2,000以上"]


# ════════════════════════════════════════════════════════════════
# 核心填寫函式
# ════════════════════════════════════════════════════════════════

def human_type(page, selector, text, min_ms=40, max_ms=120):
    """模擬人類打字速度"""
    page.click(selector)
    for ch in text:
        page.keyboard.type(ch)
        time.sleep(random.uniform(min_ms, max_ms) / 1000)

def human_delay(min_s=0.4, max_s=1.2):
    time.sleep(random.uniform(min_s, max_s))

def fill_google_form(page, persona: dict) -> dict:
    """填寫 mock_google_form.html，回傳填寫摘要"""
    result = {"name": persona["name"], "status": "failed", "answers": {}}

    # Q1 短答（平台）
    inp = page.locator("input[type='text']:visible").first
    inp.click(); inp.fill("")
    human_type(page, "input[type='text']:visible", persona["platform"])
    result["answers"]["平台"] = persona["platform"]
    human_delay()

    # Q2 段落（原因）
    ta = page.locator("textarea:visible").first
    ta.click(); ta.fill("")
    human_type(page, "textarea:visible", persona["reason"], 30, 90)
    result["answers"]["理由"] = persona["reason"][:30] + "..."
    human_delay()

    # Q3 單選（年齡）
    age_idx = AGE_MAP.get(persona["age_val"], 1)
    radios = page.locator("[role='radiogroup']:first-of-type [role='radio']").all()
    if radios and age_idx < len(radios):
        radios[age_idx].click()
        result["answers"]["年齡"] = persona["age_val"]
    human_delay(0.3, 0.8)

    # Q4 多選（保養品類型）
    all_cbs = page.locator("[role='group'] [role='checkbox']").all()
    product_names = ["乳液/乳霜", "精華液/安瓶", "面膜", "防曬", "卸妝"]
    chosen = []
    for idx in persona["products"]:
        if idx < len(all_cbs):
            all_cbs[idx].click()
            chosen.append(product_names[idx])
            human_delay(0.15, 0.4)
    result["answers"]["保養品類型"] = "、".join(chosen)

    # Q5 下拉（預算）
    budget_idx = BUDGET_LABELS.index(persona["budget"]) if persona["budget"] in BUDGET_LABELS else 1
    dd = page.locator("[role='listbox']").first
    dd.click()
    human_delay(0.3, 0.6)
    opts = page.locator("[role='option']:visible").all()
    if opts and budget_idx < len(opts):
        opts[budget_idx].click()
        result["answers"]["預算"] = persona["budget"]
    human_delay(0.3, 0.7)

    # Q6 量表（有機重視度 1–5）
    score = persona["organic_score"]
    scales = page.locator(".freebirdFormviewerViewItemsScaleScaleColumnLabel").all()
    if scales and score <= len(scales):
        scales[score - 1].click()
        result["answers"]["有機重視度"] = f"{score}/5"
    human_delay(0.4, 0.9)

    # 送出
    page.locator(".freebirdFormviewerViewNavigationSubmitButton").click()
    time.sleep(0.8)
    title = page.title()
    if "已提交" in title:
        result["status"] = "success"

    return result


# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════

def load_config(config_path: str) -> dict:
    """讀取 survey.html 匯出的 JSON 設定檔"""
    p = Path(config_path)
    if not p.exists():
        # 同目錄找
        p = BASE_DIR / config_path
    if not p.exists():
        warn(f"找不到設定檔：{config_path}，使用預設值")
        return {}
    cfg = json.loads(p.read_text(encoding="utf-8"))
    log(f"已載入設定檔：{p.name}")
    d = cfg.get("projectData", {})
    if d.get("companyName"): log(f"  案件：{d.get('companyName')} — {d.get('productName','')}", Y)
    return cfg

def filter_personas(cfg: dict) -> list:
    """依照設定檔的條件篩選 / 排序 Persona"""
    if not cfg:
        return PERSONAS
    cond = cfg.get("conditions", {})
    gender_map = {"female":"female","male":"male","nonbinary":"nonbinary"}
    age_map = {"18-24":"18-24","25-34":"25-34","35-44":"35-44","45-54":"45-54","55+":"55+"}

    def matches(p):
        if cond.get("gender","random") != "random":
            if p["gender"] != gender_map.get(cond["gender"], p["gender"]):
                return False
        if cond.get("age","random") != "random":
            if p["age_val"] != age_map.get(cond["age"], p["age_val"]):
                return False
        return True

    filtered = [p for p in PERSONAS if matches(p)]
    # 若篩完沒人，退回全部
    return filtered if filtered else PERSONAS

def run(args):
    # ── 讀取 JSON 設定檔 ─────────────────────────────────────────
    cfg = load_config(args.config) if args.config else {}
    pd = cfg.get("projectData", {})

    # --form-url 優先；其次從設定檔；最後用 mock
    form_url = (args.form_url
                or pd.get("surveyUrl","")
                or (BASE_DIR / "mock_google_form.html").as_uri())

    # --count 優先；其次從設定檔
    raw_count = args.count if args.count != 10 else cfg.get("count", args.count)
    personas = filter_personas(cfg)
    count = min(raw_count, len(personas))
    proxies = []
    if args.proxy_list:

        pf = Path(args.proxy_list)
        if pf.exists():
            proxies = [l.strip() for l in pf.read_text().splitlines() if l.strip()]
            log(f"已載入 {len(proxies)} 個 proxy IP")
        else:
            warn(f"找不到 proxy 清單：{args.proxy_list}")

    is_mock = "mock_google_form" in form_url or form_url.startswith("file://")
    case_label = pd.get("caseNote") or pd.get("companyName") or "（未指定案件）"
    log(f"\n{'═'*58}")
    log(f"  SurveyAI — 模擬填寫 {count} 份問卷")
    log(f"  案件：{case_label}")
    log(f"  表單：{'本機 Mock' if is_mock else form_url[:60]}")
    if proxies: log(f"  IP 輪換：啟用（{len(proxies)} 個 proxy）")
    else:        log(f"  IP 輪換：未啟用（本機 IP）", Y)
    log(f"{'═'*58}\n")

    results = []
    screenshots_dir = BASE_DIR / "survey_results"
    screenshots_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        for i, persona in enumerate(personas[:count]):
            n = i + 1
            log(f"[{n:02d}/{count}] {persona['name']} | {persona['age']} | {persona['occupation']}")

            # ── Proxy 設定 ─────────────────────────────────────
            proxy_cfg = None
            proxy_label = "本機 IP"
            if proxies:
                proxy_url = proxies[i % len(proxies)]
                proxy_cfg = {"server": proxy_url}
                proxy_label = proxy_url

            # ── Browser context（每份獨立）─────────────────────
            ua = USER_AGENTS[i % len(USER_AGENTS)]
            vp = VIEWPORTS[i % len(VIEWPORTS)]

            ctx_opts = dict(
                user_agent=ua,
                viewport=vp,
                locale="zh-TW",
                timezone_id="Asia/Taipei",
            )
            if proxy_cfg:
                ctx_opts["proxy"] = proxy_cfg

            browser = p.chromium.launch(headless=args.headless, slow_mo=60)
            ctx = browser.new_context(**ctx_opts)
            page = ctx.new_page()

            start_time = datetime.now()
            row = {
                "序號": n,
                "姓名": persona["name"],
                "性別": "女" if persona["gender"] == "female" else "男",
                "年齡層": persona["age_val"],
                "職業": persona["occupation"],
                "個性": persona["personality"],
                "IP": proxy_label,
                "UA裝置": "手機" if "Mobile" in ua or "iPhone" in ua else "桌機",
                "開始時間": start_time.strftime("%H:%M:%S"),
            }

            try:
                page.goto(form_url, timeout=15000)
                page.wait_for_load_state("domcontentloaded")

                # 隨機瀏覽延遲（模擬真人閱讀題目）
                human_delay(0.8, 2.5)

                result = fill_google_form(page, persona)

                end_time = datetime.now()
                elapsed = (end_time - start_time).seconds

                row.update({
                    "狀態": "✓ 成功" if result["status"] == "success" else "✗ 失敗",
                    "填寫秒數": elapsed,
                    "平台": result["answers"].get("平台", ""),
                    "年齡答案": result["answers"].get("年齡", ""),
                    "預算": result["answers"].get("預算", ""),
                    "有機重視度": result["answers"].get("有機重視度", ""),
                    "保養品類型": result["answers"].get("保養品類型", ""),
                })

                # 截圖
                shot_path = screenshots_dir / f"{n:02d}_{persona['name']}.png"
                page.screenshot(path=str(shot_path), full_page=True)
                row["截圖"] = shot_path.name

                if result["status"] == "success":
                    ok(f"  成功 | 耗時 {elapsed}s | 截圖：{shot_path.name}")
                else:
                    warn(f"  狀態未確認（可能仍成功）")

            except Exception as e:
                row["狀態"] = f"✗ 錯誤：{str(e)[:40]}"
                err(f"  錯誤：{e}")

            results.append(row)
            browser.close()

            # 份數間隔（模擬真實節奏，非最後一份）
            if n < count:
                gap = random.uniform(1.5, 4.0) if is_mock else random.uniform(15, 45)
                label = f"{gap:.1f}秒" if is_mock else f"{gap:.0f}秒"
                log(f"  等待 {label} 後填下一份...", Y)
                time.sleep(gap)

    # ── 輸出 CSV ────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = BASE_DIR / f"survey_results_{ts}.csv"
    if results:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    # ── 最終報告 ────────────────────────────────────────────────
    success = sum(1 for r in results if "成功" in r.get("狀態", ""))
    log(f"\n{'═'*58}")
    log(f"  完成！{success}/{count} 份成功", G)
    log(f"  截圖資料夾：{screenshots_dir.name}/")
    log(f"  CSV 結果：{csv_path.name}", G)
    log(f"{'═'*58}\n")

    # 印出摘要表
    log("  填寫摘要：", B)
    log(f"  {'#':>3} {'姓名':<8} {'年齡':<8} {'預算':<12} {'有機':>5} {'狀態'}", B)
    log(f"  {'─'*52}", B)
    for r in results:
        log(f"  {r['序號']:>3} {r['姓名']:<8} {r['年齡層']:<8} {r.get('預算',''):<12} "
            f"{r.get('有機重視度',''):>5}  {r['狀態']}", G if "成功" in r['狀態'] else R)

    return csv_path


# ════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless",    action="store_true", help="無頭模式")
    parser.add_argument("--proxy-list",  metavar="FILE",      help="proxy 清單檔案路徑")
    parser.add_argument("--form-url",    metavar="URL",       help="自訂表單 URL（優先於設定檔）")
    parser.add_argument("--count",       type=int, default=10,help="份數（優先於設定檔）")
    parser.add_argument("--config",      metavar="FILE",      help="survey.html 匯出的 JSON 設定檔")
    args = parser.parse_args()
    run(args)
