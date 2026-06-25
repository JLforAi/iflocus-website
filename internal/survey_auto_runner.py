"""
SurveyAI local survey auto runner.

MVP scope:
- Fill and submit Google Forms / SurveyCake style pages with Playwright.
- Read SurveyAI JSON settings and JSON/CSV response rows.
- Split work across multiple people with worker-index / worker-total.
- Print local scheduling commands for Windows Task Scheduler or Python loop mode.

Examples:
  python -X utf8 survey_auto_runner.py --form-url "file:///.../mock_google_form.html" --count 3 --headless
  python -X utf8 survey_auto_runner.py --config case-settings.json --form-url "https://forms.gle/..." --worker-index 1 --worker-total 3
  python -X utf8 survey_auto_runner.py --print-schedule --form-url "https://..." --count 70 --daily-count 10 --days 7
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, sync_playwright


BASE_DIR = Path(__file__).parent
DEFAULT_STATE = BASE_DIR / ".survey_auto_state.json"
DEFAULT_REPORT_DIR = BASE_DIR / "survey_auto_results"

# ===== 模擬 Email 產生器 =====
_SURNAMES = [
    "lin","chen","huang","zhang","li","wang","wu","liu","cai","yang",
    "xu","zheng","xie","hong","guo","zhu","ye","luo","liao","jiang",
    "lu","fan","fang","su","zeng","hsieh","tang","cheng","hsu","kuo",
]
_GIVEN = [
    "wei","ting","yu","jia","yi","xin","zhen","min","hui","ling",
    "jie","jun","kai","hao","yan","mei","fang","ya","xuan","qi",
    "zhi","rui","en","si","le","tzu","pei","wan","hsiao","chun",
]
_DOMAINS = [
    "gmail.com","gmail.com","gmail.com",  # weighted higher
    "yahoo.com.tw","yahoo.com.tw",
    "hotmail.com","outlook.com",
    "icloud.com","pchome.com.tw","hinet.net",
]

def generate_email(index: int) -> str:
    """Return a realistic-looking but fake email for the given index."""
    rng = random.Random(index * 7919 + 42)
    surname = rng.choice(_SURNAMES)
    given   = rng.choice(_GIVEN)
    domain  = rng.choice(_DOMAINS)
    sep     = rng.choice([".", "_", ""])
    suffix  = str(rng.randint(1, 99)) if rng.random() < 0.4 else ""
    return f"{surname}{sep}{given}{suffix}@{domain}"


# ===== 繁體中文 AI 模擬文字池 =====
_ZH_SHORT = [
    "通常透過社群媒體得知新產品",
    "習慣在購買前比較多個品牌",
    "重視產品成分的安全與透明度",
    "朋友推薦是我選擇產品的主要依據",
    "偏好有口碑且評價穩定的品牌",
    "會先看消費者評論再決定是否購買",
    "注重性價比，不一定選最貴的",
    "喜歡嘗試新品牌，願意接受新事物",
    "對於有機、天然成分特別有興趣",
    "常在網路平台上搜尋產品資訊",
    "購買前會確認是否有過敏成分",
    "重視售後服務與品牌的回應速度",
    "習慣在促銷活動期間集中採購",
    "偏好小包裝試用品，降低嘗試風險",
    "會關注品牌的環保與永續理念",
    "透過 YouTube 開箱影片了解產品",
    "看到熟悉的明星代言會增加信任感",
    "優先選擇台灣本土製造的產品",
    "注重包裝設計，視覺美觀也很重要",
    "重視產品效果，願意為品質多付費",
]

_ZH_LONG = [
    "我在選購產品時，最在意的是成分的安全性與品牌透明度。如果廠商能清楚標示原料來源，並提供第三方檢驗報告，我的購買意願會大幅提升。",
    "價格固然重要，但產品的實際效果才是我持續回購的關鍵。我通常會先購買試用裝評估，若效果符合預期，才考慮購買正裝。",
    "社群媒體的口碑對我影響很大，特別是素人真實使用心得。與其相信廣告宣傳，我更傾向參考與自己膚質或需求相近的消費者評論。",
    "我希望品牌能夠提供更多客製化的產品選擇，因為每個人的需求都不同。一刀切的產品難以滿足所有消費者，多樣化的選擇更能吸引我嘗試。",
    "產品包裝的設計與環保性對我而言同樣重要。如果品牌使用可回收材質或提供補充包，我會更願意長期支持這個品牌。",
    "我認為品牌與消費者的互動非常重要，快速且有誠意的客服回應讓我感到被重視。有問題能即時獲得解答，購物體驗會更加安心。",
    "除了產品本身，我也很在意購買流程是否便利。一個操作簡單、付款安全、配送準時的購物環境，會讓我更樂意再次光顧。",
    "我傾向於選擇有科學研究背書或皮膚科醫師推薦的產品，這類認證能有效降低我嘗試新品的疑慮，建立品牌在我心中的可信度。",
    "朋友的口碑介紹是促使我初次購買的最大推力。如果身邊有人推薦並分享親身體驗，我會比看任何廣告都更快下定購買決心。",
    "我期待品牌能定期推出會員專屬優惠或積點回饋機制，這樣不只能增加我的忠誠度，也讓我感覺花的每一分錢都更有價值。",
    "對我來說，產品的香味和使用質地非常影響購買意願。即使成分再好，如果氣味令人不舒服或質地太黏稠，我也很難堅持使用。",
    "我希望品牌能在廣告中使用更真實、多元的形象，而非只追求完美濾鏡。真實呈現產品使用效果，更能建立消費者長期的信任感。",
    "促銷折扣固然吸引人，但如果品牌過於頻繁打折，反而會讓我懷疑產品的原始定價是否合理，甚至降低對品牌價值的認同感。",
    "我認為試用包或小樣的提供非常重要，讓消費者在正式購買前有機會評估產品的適合度，這樣能有效降低購買錯誤的風險。",
    "我在購買時會特別查看產品是否通過相關安全認證，例如不含有害化學物質的認證，這些標章能大幅提升我對產品的信心。",
    "我重視品牌的故事與理念，若品牌能傳達明確的價值觀，例如支持在地農業或關懷弱勢族群，我會更有動力選擇該品牌的產品。",
    "使用體驗的一致性很重要，每次購買的產品品質都應維持在相同水準。若某批產品的品質明顯下降，我可能就不會再回購了。",
    "我希望品牌能提供更清楚的使用說明與教學資源，例如影片示範或圖文步驟，讓初次使用者能快速上手並發揮產品最佳效果。",
    "在眾多選擇中，品牌的視覺識別與整體美感也是影響我購買決策的因素之一，精緻的包裝設計讓我願意花時間進一步了解產品。",
    "我會定期追蹤喜愛品牌的社群帳號，希望能第一時間得知新品上市、限定優惠或品牌活動，這種互動讓我對品牌更有歸屬感。",
]


def generate_zh_text(index: int, field: str = "short") -> str:
    """Return a varied Traditional Chinese text for the given response index."""
    rng = random.Random(index * 3571 + (17 if field == "short" else 89))
    pool = _ZH_SHORT if field == "short" else _ZH_LONG
    return rng.choice(pool)


DEFAULT_RESPONSES = [
    {
        "name": "受訪者甲",
        "email": "respondent.a@example.com",
        "short_text": "通常透過社群媒體得知新產品",
        "long_text": "我在選購產品時，最在意的是成分的安全性與品牌透明度。如果廠商能清楚標示原料來源，並提供第三方檢驗報告，我的購買意願會大幅提升。",
        "radio": "25-34",
        "checkbox": "ig",
        "select": "500-1000",
        "rating": "4",
        "nps": "8",
        "slider": "45",
    },
    {
        "name": "受訪者乙",
        "email": "respondent.b@example.com",
        "short_text": "習慣在購買前比較多個品牌",
        "long_text": "社群媒體的口碑對我影響很大，特別是素人真實使用心得。與其相信廣告宣傳，我更傾向參考與自己需求相近的消費者評論。",
        "radio": "35-44",
        "checkbox": "review",
        "select": "1000-2000",
        "rating": "5",
        "nps": "9",
        "slider": "55",
    },
    {
        "name": "受訪者丙",
        "email": "respondent.c@example.com",
        "short_text": "注重性價比，不一定選最貴的",
        "long_text": "品牌與消費者的互動非常重要，快速且有誠意的客服回應讓我感到被重視。有問題能即時獲得解答，購物體驗會更加安心。",
        "radio": "18-24",
        "checkbox": "yt",
        "select": "500-",
        "rating": "3",
        "nps": "7",
        "slider": "35",
    },
]


@dataclass
class RunOptions:
    form_url: str
    platform: str
    count: int
    headless: bool
    submit: bool
    manual_submit: bool
    use_chrome: bool
    interval_min_sec: float
    interval_max_sec: float
    worker_index: int
    worker_total: int
    job_id: str
    state_file: Path
    report_dir: Path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_responses(config_path: Path | None, responses_path: Path | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config: dict[str, Any] = {}
    responses: list[dict[str, Any]] = []

    if config_path:
        config = load_json(resolve_path(config_path))
        if isinstance(config.get("responses"), list):
            responses = [dict(row) for row in config["responses"] if isinstance(row, dict)]

    if responses_path:
        resolved = resolve_path(responses_path)
        if resolved.suffix.lower() == ".csv":
            responses = load_csv(resolved)
        else:
            data = load_json(resolved)
            if isinstance(data, list):
                responses = [dict(row) for row in data if isinstance(row, dict)]
            elif isinstance(data.get("responses"), list):
                responses = [dict(row) for row in data["responses"] if isinstance(row, dict)]

    return config, responses or DEFAULT_RESPONSES


def resolve_path(path: Path) -> Path:
    if path.exists():
        return path
    candidate = BASE_DIR / path
    if candidate.exists():
        return candidate
    return path


def detect_platform(url: str, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    lower = url.lower()
    if "surveycake" in lower or "mock_surveycake" in lower:
        return "surveycake"
    return "google"


def response_for_index(responses: list[dict[str, Any]], index: int) -> dict[str, Any]:
    row = dict(responses[index % len(responses)])
    row.setdefault("response_index", index + 1)
    return row


def slice_for_worker(total: int, worker_index: int, worker_total: int) -> range:
    if worker_total < 1:
        raise ValueError("--worker-total must be >= 1")
    if worker_index < 1 or worker_index > worker_total:
        raise ValueError("--worker-index must be between 1 and --worker-total")
    start = math.floor(total * (worker_index - 1) / worker_total)
    end = math.floor(total * worker_index / worker_total)
    return range(start, end)


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"submitted": []}
    try:
        state = load_json(path)
        if not isinstance(state.get("submitted"), list):
            state["submitted"] = []
        return state
    except Exception:
        return {"submitted": []}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def submission_key(job_id: str, worker_index: int, response_index: int) -> str:
    raw = f"{job_id}|worker:{worker_index}|response:{response_index}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def fill_first_text_fields(page: Page, row: dict[str, Any]) -> int:
    short_text = row.get("short_text") or row.get("name") or "SurveyAI test response"
    long_text  = row.get("long_text") or row.get("reason") or "This is an automated test response."
    email      = row.get("email") or "respondent@example.com"
    filled = 0
    text_idx = 0
    text_values = [short_text, long_text, short_text]
    fields = page.locator("input[type='text']:visible, input[type='email']:visible, textarea:visible").all()
    for field in fields:
        try:
            meta = field.evaluate("""el => {
                const subjectType = (el.closest('[data-subject-type]') || {}).getAttribute?.('data-subject-type') || '';
                const subjectTitle = (el.closest('[data-subject-type]')?.querySelector('[aria-label=\"slate html\"]')?.innerText || '').toLowerCase();
                return {
                    inputType: (el.type || '').toLowerCase(),
                    placeholder: (el.placeholder || '').toLowerCase(),
                    name: (el.name || el.id || '').toLowerCase(),
                    subjectType: subjectType.toLowerCase(),
                    subjectTitle: subjectTitle
                };
            }""")
            print(f"  [field] type={meta['inputType']} subjectType={meta['subjectType']} title={meta['subjectTitle'][:30]}", flush=True)
            is_email = (
                meta["inputType"] == "email"
                or meta["subjectType"] == "email"
                or any(kw in meta["placeholder"] for kw in ["email", "e-mail", "信箱", "@"])
                or any(kw in meta["name"] for kw in ["email", "mail"])
                or any(kw in meta["subjectTitle"] for kw in ["email", "e-mail", "信箱"])
            )
            if is_email:
                field.fill(email)
            else:
                field.fill(str(text_values[min(text_idx, len(text_values) - 1)]))
                text_idx += 1
            filled += 1
        except Exception:
            pass
    return filled


def click_option_by_value(options, wanted: Any, fallback_index: int = 0) -> bool:
    wanted_text = str(wanted or "").lower()
    all_options = options.all()
    if not all_options:
        return False
    for option in all_options:
        data_val = (option.get_attribute("data-val") or option.inner_text() or "").lower()
        if wanted_text and wanted_text in data_val:
            option.click()
            return True
    all_options[min(fallback_index, len(all_options) - 1)].click()
    return True


def fill_google(page: Page, row: dict[str, Any], submit: bool) -> dict[str, Any]:
    page.wait_for_selector("body", timeout=15000)
    filled = fill_first_text_fields(page, row)

    listitems = page.locator("[role='listitem'], .freebirdFormviewerViewItemsItemItem").all()
    for item in listitems:
        radios = item.locator("[role='radio']:visible")
        if radios.count() and click_option_by_value(radios, row.get("radio"), fallback_index=1):
            filled += 1

        checkboxes = item.locator("[role='checkbox']:visible")
        if checkboxes.count() and click_option_by_value(checkboxes, row.get("checkbox"), fallback_index=0):
            filled += 1

        listboxes = item.locator("[role='listbox']:visible")
        if listboxes.count():
            listboxes.first.click()
            page.wait_for_timeout(150)
            options = page.locator("[role='option']:visible")
            if click_option_by_value(options, row.get("select"), fallback_index=1):
                filled += 1

    scale_buttons = page.locator(".freebirdFormviewerViewItemsScaleScaleColumnLabel:visible")
    if scale_buttons.count():
        rating = int(row.get("rating") or 4)
        scale_buttons.nth(max(0, min(rating - 1, scale_buttons.count() - 1))).click()
        filled += 1

    submitted = False
    if submit:
        submit_button = page.locator(".freebirdFormviewerViewNavigationSubmitButton, div[role='button']:has-text('Submit'), button:has-text('Submit')").first
        submit_button.click()
        submitted = wait_for_success(page, ["#submit-result", "Google Forms Mock"])

    return {"filled": filled, "submitted": submitted}


def fill_surveycake(page: Page, row: dict[str, Any], submit: bool, manual_submit: bool = False) -> dict[str, Any]:
    """
    Multi-page SurveyCake filler.
    Uses JS to interact with hidden radio/checkbox inputs (SurveyCake renders
    custom-styled options on top of real inputs), then clicks next/submit buttons
    by visible text to navigate through all pages.
    """
    page.wait_for_selector("body", timeout=20000)
    page.wait_for_timeout(2000)  # wait for React/JS to render

    # --- click "開始" / "Start" intro button if present ---
    for start_sel in [
        "button:has-text('開始')",
        "button:has-text('Start')",
        "a:has-text('開始')",
    ]:
        try:
            btn = page.locator(start_sel).first
            if btn.is_visible(timeout=1500):
                btn.click()
                page.wait_for_timeout(2000)
                break
        except Exception:
            pass

    # --- debug: save HTML so we can inspect real selectors ---
    try:
        debug_path = BASE_DIR / "debug_page1.html"
        debug_path.write_text(page.content(), encoding="utf-8")
    except Exception:
        pass

    # --- debug: print what radio/checkbox inputs are found ---
    try:
        info = page.evaluate("""() => {
            const radios = document.querySelectorAll('input[type="radio"]');
            const checks = document.querySelectorAll('input[type="checkbox"]');
            const btns   = Array.from(document.querySelectorAll('button')).map(b=>b.innerText.trim()).filter(t=>t);
            return {radios: radios.length, checks: checks.length, buttons: btns.slice(0,10)};
        }""")
        print(f"  [debug] radio inputs={info['radios']}, checkbox inputs={info['checks']}, buttons={info['buttons']}")
        sys.stdout.flush()
    except Exception:
        pass

    filled = 0
    max_pages = 30  # safety limit
    import random as _rnd

    def _human_pause(min_ms: int, max_ms: int):
        """模擬真人的隨機停頓"""
        page.wait_for_timeout(_rnd.randint(min_ms, max_ms))

    def _random_mouse_move():
        """隨機滑鼠移動，模擬真人視線轉移"""
        try:
            vp = page.viewport_size or {"width": 1280, "height": 720}
            for _ in range(_rnd.randint(2, 4)):
                page.mouse.move(_rnd.randint(100, vp["width"]-100), _rnd.randint(100, vp["height"]-100), steps=_rnd.randint(5, 15))
                page.wait_for_timeout(_rnd.randint(100, 400))
        except Exception:
            pass

    for _page_num in range(max_pages):
        # 進入頁面後：閱讀時間 3-8 秒（真人讀題）
        _human_pause(3000, 8000)
        _random_mouse_move()

        # --- fill text / email inputs, detecting email by question context ---
        short_text = row.get("short_text") or "通常透過社群媒體得知新產品"
        long_text  = row.get("long_text") or "我在選購產品時最在意成分的安全性與品牌透明度，也會參考其他消費者的真實評論。"
        email_val  = row.get("email") or "respondent@example.com"
        try:
            page.evaluate(f"""(args) => {{
                const [shortText, longText, emailVal] = args;
                let textIdx = 0;
                const textValues = [shortText, longText, shortText];
                const fields = document.querySelectorAll(
                    'input[type="text"]:not([disabled]), input[type="email"]:not([disabled]), textarea:not([disabled])'
                );
                const allVisible = Array.from(fields).filter(el => el.offsetParent !== null);
                allVisible.forEach((el, elIdx) => {{
                    // 取得周圍文字（多層往上找，確保讀到有意義的內容）
                    const subject = el.closest('[data-subject-type]');
                    let contextText = (subject?.innerText || '').toLowerCase();
                    if (!contextText || contextText.length < 5) {{
                        let p = el.parentElement;
                        for (let i = 0; i < 6 && p; i++, p = p.parentElement) {{
                            const t = (p.innerText || '').toLowerCase();
                            if (t.length > 5) {{ contextText = t; break; }}
                        }}
                    }}
                    // placeholder：先用 getAttribute 再用 .placeholder
                    const placeholder = (el.getAttribute('placeholder') || el.placeholder || '').toLowerCase();
                    const nameAttr = (el.name || el.id || '').toLowerCase();
                    const isLastField = elIdx === allVisible.length - 1;
                    const isOnlyField = allVisible.length === 1;
                    const isEmail = el.type === 'email'
                        || contextText.includes('email')
                        || contextText.includes('信箱')      // 電子信箱、請填入電子信箱
                        || contextText.includes('電子郵件')
                        || contextText.includes('郵箱')
                        || contextText.includes('e-mail')
                        || contextText.includes('抽獎')
                        || contextText.includes('幸運')
                        || contextText.includes('禮')
                        || contextText.includes('聯絡')
                        || placeholder.includes('email')
                        || placeholder.includes('信箱')      // 請填入電子信箱
                        || placeholder.includes('郵件')
                        || nameAttr.includes('email')
                        || nameAttr.includes('mail')
                        || (isLastField && textIdx >= 1)
                        || (isOnlyField && isLastField);
                    const val = isEmail ? emailVal : textValues[Math.min(textIdx, textValues.length-1)];
                    if (!isEmail) textIdx++;
                    // Set value via React-compatible native setter
                    const proto = el.tagName === 'TEXTAREA'
                        ? window.HTMLTextAreaElement.prototype
                        : window.HTMLInputElement.prototype;
                    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event('input', {{bubbles:true}}));
                    el.dispatchEvent(new Event('change', {{bubbles:true}}));
                }});
            }}""", [short_text, long_text, email_val])
            filled += 1
        except Exception:
            pass

        # --- 用 Playwright keyboard.type() 模擬真人逐字輸入 email（最能觸發 React onChange）---
        for email_sel in [
            "input[placeholder*='信箱']",
            "input[placeholder*='mail' i]",
            "input[placeholder*='電子']",
            "input[placeholder*='Email']",
            "input[placeholder*='email']",
        ]:
            try:
                loc = page.locator(email_sel).first
                if loc.is_visible(timeout=600):
                    # 1. 三擊全選清空舊值
                    loc.click(click_count=3, timeout=600)
                    page.wait_for_timeout(150)
                    page.keyboard.press("Delete")
                    page.wait_for_timeout(150)
                    # 2. 模擬真人逐字輸入（每字 50ms 延遲，觸發 React onChange）
                    page.keyboard.type(email_val, delay=50)
                    page.wait_for_timeout(200)
                    # 3. Tab 移開觸發 blur 事件
                    page.keyboard.press("Tab")
                    page.wait_for_timeout(300)
                    break
            except Exception:
                pass

        # --- click SurveyCake options via data-subject-option-id (no standard inputs) ---
        try:
            n = page.evaluate("""() => {
                let clicked = 0;
                const seed = Math.random();
                const subjects = document.querySelectorAll('[data-subject-type][data-subject-id]');
                subjects.forEach(subject => {
                    const type = subject.getAttribute('data-subject-type');
                    if (!type || type === 'QUOTE' || type === 'STATEMENT') return;
                    const options = Array.from(subject.querySelectorAll('[data-subject-option-id]'));
                    if (options.length === 0) return;
                    if (type === 'CHOICEONE') {
                        const alreadyDone = options.some(el => el.className.includes('selected') || el.className.includes('active'));
                        if (alreadyDone) return;
                        const idx = Math.max(1, Math.floor(seed * options.length)) % options.length;
                        options[idx].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}));
                        clicked++;
                    } else {
                        const idx = Math.floor(seed * options.length) % options.length;
                        options[idx].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}));
                        clicked++;
                        if (options.length > 2 && seed > 0.4) {
                            options[(idx + 2) % options.length].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}));
                            clicked++;
                        }
                    }
                });
                return clicked;
            }""")
            filled += n or 0
        except Exception:
            pass
        page.wait_for_timeout(500)  # let React state update after clicks

        # 填完後：檢查時間 2-5 秒
        _human_pause(2000, 5000)
        _random_mouse_move()

        # --- try to click "下一頁" / "下一步" ---
        next_btn = None
        for sel in [
            "button:has-text('下一頁')",
            "button:has-text('下一步')",
            "a:has-text('下一頁')",
            "input[type='button'][value*='下一']",
        ]:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=500):
                    next_btn = loc
                    break
            except Exception:
                pass

        if next_btn:
            try:
                next_btn.scroll_into_view_if_needed()
                next_btn.click()
                page.wait_for_timeout(2000)
                continue  # go to next page loop
            except Exception:
                pass

        # --- no next button: look for submit ---
        submitted = False
        submit_visible = False
        for sel in ["button:has-text('送出')", "button:has-text('提交')", "button:has-text('完成')", "button:has-text('Submit')", "input[type='submit']"]:
            try:
                if page.locator(sel).first.is_visible(timeout=500):
                    submit_visible = True
                    break
            except Exception:
                pass

        if submit_visible:
            if manual_submit:
                # 半自動模式：注入頁面上的紅色橫條提示 + 輪詢等待網頁變化
                print("\n" + "="*60)
                print("✋ 已填完所有題目，請在【瀏覽器】中：")
                print("   1. 確認 email 欄位已填入正確地址")
                print("   2. 手動點擊「送出」或「確定送出」")
                print("   3. 出現感謝頁面後，腳本會自動偵測並繼續")
                print("   （最多等 15 分鐘，逾時會自動結束）")
                print("="*60)
                sys.stdout.flush()
                # 在頁面上方注入顯眼紅色提示條
                try:
                    page.evaluate("""() => {
                        const bar = document.createElement('div');
                        bar.id = '__survey_ai_banner__';
                        bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:999999;background:#ff4444;color:white;padding:16px;text-align:center;font-size:18px;font-weight:bold;box-shadow:0 2px 10px rgba(0,0,0,.3);';
                        bar.textContent = '✋ 自動填寫完成！請確認 email 後手動點「送出」';
                        document.body.appendChild(bar);
                    }""")
                except Exception:
                    pass
                # 輪詢偵測：URL 變化、感謝文字出現、或送出按鈕消失
                import time as _time
                start_t = _time.time()
                start_url = page.url
                manual_done = False
                while _time.time() - start_t < 900:  # 15 分鐘
                    try:
                        if page.url != start_url:
                            manual_done = True; break
                        body_text = page.evaluate("() => document.body ? document.body.innerText : ''") or ""
                        if "感謝您的填寫" in body_text and "請點擊下方按鈕" not in body_text:
                            manual_done = True; break
                        if "問卷已送出" in body_text or "已完成填寫" in body_text:
                            manual_done = True; break
                        # 檢查送出按鈕還在不在
                        still_has_submit = False
                        for s in ["button:has-text('送出')", "button:has-text('確定送出')"]:
                            try:
                                if page.locator(s).first.is_visible(timeout=200):
                                    still_has_submit = True; break
                            except Exception:
                                pass
                        if not still_has_submit and _time.time() - start_t > 5:
                            manual_done = True; break
                    except Exception:
                        pass
                    _time.sleep(2)
                if manual_done:
                    print(">>> 偵測到送出完成，繼續...", flush=True)
                else:
                    print(">>> 逾時，請確認是否實際送出", flush=True)
                submitted = manual_done
            elif submit:
                for sel in ["button:has-text('送出')", "button:has-text('提交')", "button:has-text('完成')", "button:has-text('Submit')", "input[type='submit']"]:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible(timeout=500):
                            loc.scroll_into_view_if_needed()
                            loc.click()
                            page.wait_for_timeout(5000)
                            submitted = True
                            break
                    except Exception:
                        pass

        return {"filled": filled, "submitted": submitted}

    return {"filled": filled, "submitted": False}


def wait_for_success(page: Page, markers: list[str]) -> bool:
    for marker in markers:
        try:
            if marker.startswith("#"):
                page.wait_for_selector(marker, state="visible", timeout=3000)
                return True
            page.wait_for_function(
                "(marker) => document.body.innerText.includes(marker) || document.title.includes(marker) || !!document.getElementById(marker)",
                marker,
                timeout=3000,
            )
            return True
        except PlaywrightTimeout:
            continue
    return False


def run_submissions(options: RunOptions, responses: list[dict[str, Any]], email_by_index: dict[int, str] | None = None) -> list[dict[str, Any]]:
    state = load_state(options.state_file)
    submitted_keys = set(state.get("submitted", []))
    indices = list(slice_for_worker(options.count, options.worker_index, options.worker_total))
    results: list[dict[str, Any]] = []
    options.report_dir.mkdir(parents=True, exist_ok=True)

    total = len(indices)
    print(f"[開始] 本機負責 {total} 份，共 {options.count} 份（平台：{options.platform}）")
    print(f"[設定] 每份間隔 {int(options.interval_min_sec)}–{int(options.interval_max_sec)} 秒，無頭模式：{options.headless}")
    sys.stdout.flush()

    with sync_playwright() as p:
        if options.use_chrome:
            # 使用本機 Chrome（有真實 cookie/歷史），讓 Cloudflare 認為是真人
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
            chrome_exe = next((p_ for p_ in chrome_paths if Path(p_).exists()), None)
            user_data = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
            if chrome_exe:
                print(f"[Chrome] 使用本機 Chrome：{chrome_exe}")
                sys.stdout.flush()
                # 用 channel="chrome" 啟動真實 Chrome 二進制（指紋與 Chromium 不同）
                browser = p.chromium.launch(
                    channel="chrome",
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ],
                    ignore_default_args=["--enable-automation"],
                )
                use_persistent = False
            else:
                print("[Chrome] 找不到 Chrome，改用 Playwright Chromium")
                browser = p.chromium.launch(headless=options.headless)
                use_persistent = False
        else:
            browser = p.chromium.launch(
                headless=options.headless,
                args=["--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            use_persistent = False
        for local_no, response_index in enumerate(indices, start=1):
            key = submission_key(options.job_id, options.worker_index, response_index)
            if key in submitted_keys:
                print(f"[{local_no}/{total}] 跳過（已送出過）")
                sys.stdout.flush()
                results.append({"response_index": response_index + 1, "status": "skipped_duplicate"})
                continue

            print(f"[{local_no}/{total}] 開始填寫... ", end="", flush=True)
            if use_persistent:
                # persistent context 本身就是 context，直接開新頁
                context = browser
                page = browser.new_page()
            else:
                context = browser.new_context(locale="zh-TW", timezone_id="Asia/Taipei")
                page = context.new_page()
            row = dict(response_for_index(responses, response_index))
            if email_by_index and response_index in email_by_index:
                row["email"] = email_by_index[response_index]
            # 依 index 自動生成不同繁體中文填答文字
            if not row.get("short_text") or row.get("short_text") in ("一般消費者",):
                row["short_text"] = generate_zh_text(response_index, "short")
            if not row.get("long_text") or row.get("long_text") in ("品質和價格都很重要",):
                row["long_text"] = generate_zh_text(response_index, "long")
            started = datetime.now()
            status = "failed"
            detail: dict[str, Any] = {}
            try:
                page.goto(options.form_url, wait_until="domcontentloaded", timeout=30000)
                # Re-detect platform from actual URL after redirect
                actual_url = page.url.lower()
                platform = options.platform
                if platform == "auto" or ("pse.is" in options.form_url.lower() or "bit.ly" in options.form_url.lower() or "reurl" in options.form_url.lower()):
                    if "surveycake" in actual_url:
                        platform = "surveycake"
                    else:
                        platform = "google"

                if platform == "surveycake":
                    detail = fill_surveycake(page, row, options.submit, options.manual_submit)
                else:
                    detail = fill_google(page, row, options.submit)

                if detail.get("submitted"):
                    status = "submitted"
                    submitted_keys.add(key)
                    state["submitted"] = sorted(submitted_keys)
                    save_state(options.state_file, state)
                elif not options.submit:
                    status = "filled_no_submit"
                    submitted_keys.add(key)
                    state["submitted"] = sorted(submitted_keys)
                    save_state(options.state_file, state)
            except Exception as exc:
                detail = {"error": str(exc)}
            finally:
                screenshot = options.report_dir / f"{options.job_id}_w{options.worker_index}_{response_index + 1}.png"
                try:
                    page.screenshot(path=str(screenshot), full_page=True)
                except Exception:
                    screenshot = Path("")
                if not use_persistent:
                    context.close()
                else:
                    try:
                        page.close()
                    except Exception:
                        pass

            elapsed = round((datetime.now() - started).total_seconds(), 1)
            if status == "submitted":
                print(f"✓ 送出成功（{elapsed}s）")
            elif status == "filled_no_submit":
                print(f"✓ 填寫完成，未送出（{elapsed}s）")
            else:
                err = detail.get("error", "")
                print(f"✗ 失敗（{elapsed}s）{': ' + err[:80] if err else ''}")
            sys.stdout.flush()

            results.append(
                {
                    "response_index": response_index + 1,
                    "worker_index": options.worker_index,
                    "status": status,
                    "filled": detail.get("filled", 0),
                    "submitted": detail.get("submitted", False),
                    "seconds": elapsed,
                    "screenshot": screenshot.name,
                    "error": detail.get("error", ""),
                }
            )

            if local_no < len(indices):
                pause = random.uniform(options.interval_min_sec, options.interval_max_sec)
                if pause > 0:
                    print(f"  → 等待 {int(pause)} 秒後繼續...")
                    sys.stdout.flush()
                    time.sleep(pause)
        if use_persistent:
            browser.close()
        else:
            browser.close()

    write_report(options.report_dir, options.job_id, results)
    return results


def write_report(report_dir: Path, job_id: str, rows: list[dict[str, Any]]) -> Path:
    path = report_dir / f"{job_id}_run_report.csv"
    if not rows:
        return path
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def parse_start_date(value: str | None) -> date:
    return date.fromisoformat(value) if value else date.today()


def compute_days(start: date, end_value: str | None, days_value: int | None) -> int:
    if end_value:
        end = date.fromisoformat(end_value)
        return max(1, (end - start).days + 1)
    return max(1, days_value or 1)


def schedule_plan(args: argparse.Namespace) -> list[dict[str, Any]]:
    start = parse_start_date(args.start_date)
    inferred_days = args.days
    if args.daily_count and not inferred_days and not args.end_date:
        inferred_days = math.ceil(args.count / args.daily_count)
    days = compute_days(start, args.end_date, inferred_days)
    remaining = args.count
    plan = []
    for offset in range(days):
        if remaining <= 0:
            break
        run_date = start + timedelta(days=offset)
        daily = min(args.daily_count or remaining, remaining)
        remaining -= daily
        plan.append({"date": run_date.isoformat(), "count": daily, "time": f"{args.start_hour:02d}:00"})
    return plan


def build_runner_command(args: argparse.Namespace, count: int) -> str:
    parts = [
        "python -X utf8 survey_auto_runner.py",
        f"--form-url {quote_arg(args.form_url)}",
        f"--platform {args.platform}",
        f"--count {count}",
        f"--worker-index {args.worker_index}",
        f"--worker-total {args.worker_total}",
        f"--interval-min-sec {args.interval_min_sec}",
        f"--interval-max-sec {args.interval_max_sec}",
    ]
    if args.config:
        parts.append(f"--config {quote_arg(str(args.config))}")
    if args.responses:
        parts.append(f"--responses {quote_arg(str(args.responses))}")
    if args.headless:
        parts.append("--headless")
    if args.no_submit:
        parts.append("--no-submit")
    return " ".join(parts)


def quote_arg(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def print_schedule(args: argparse.Namespace) -> None:
    print("Local scheduling reminder:")
    print("- The execution computer must stay powered on, awake, online, and signed in when the task runs.")
    print("- If the computer sleeps, loses network, or closes during a scheduled day, that day's submissions will not run.")
    print("")
    for idx, item in enumerate(schedule_plan(args), start=1):
        task_name = f"SurveyAI_{args.job_id}_day{idx}"
        command = build_runner_command(args, item["count"])
        if args.scheduler == "windows":
            print(
                f'schtasks /Create /TN "{task_name}" /SC ONCE /ST {item["time"]} /SD {item["date"]} '
                f"/TR '{command}' /F"
            )
        else:
            print(f'{item["date"]} {item["time"]} -> {command}')


def create_windows_tasks(args: argparse.Namespace) -> None:
    if sys.platform != "win32":
        raise RuntimeError("--create-windows-tasks is only supported on Windows")
    for idx, item in enumerate(schedule_plan(args), start=1):
        task_name = f"SurveyAI_{args.job_id}_day{idx}"
        command = build_runner_command(args, item["count"])
        subprocess.run(
            [
                "schtasks",
                "/Create",
                "/TN",
                task_name,
                "/SC",
                "ONCE",
                "/ST",
                item["time"],
                "/SD",
                item["date"],
                "/TR",
                command,
                "/F",
            ],
            check=True,
        )


def build_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SurveyAI local Google Forms / SurveyCake auto runner")
    parser.add_argument("--form-url", default="", help="Google Forms or SurveyCake URL")
    parser.add_argument("--platform", choices=["auto", "google", "surveycake"], default="auto")
    parser.add_argument("--config", type=Path, help="SurveyAI exported JSON settings")
    parser.add_argument("--responses", type=Path, help="JSON/CSV response rows")
    parser.add_argument("--count", type=int, default=1, help="Total submissions for this job")
    parser.add_argument("--daily-count", type=int, default=0, help="Submissions per scheduled day")
    parser.add_argument("--start-date", help="YYYY-MM-DD")
    parser.add_argument("--end-date", help="YYYY-MM-DD")
    parser.add_argument("--days", type=int, help="Number of days to schedule")
    parser.add_argument("--start-hour", type=int, default=9, help="Daily task hour, 0-23")
    parser.add_argument("--interval-min-sec", type=float, default=30)
    parser.add_argument("--interval-max-sec", type=float, default=90)
    parser.add_argument("--worker-index", type=int, default=1)
    parser.add_argument("--worker-total", type=int, default=1)
    parser.add_argument("--job-id", default="")
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--no-submit", action="store_true")
    parser.add_argument("--manual-submit", action="store_true", help="填完後暫停，讓使用者手動點送出按鈕（解決 Cloudflare 驗證問題）")
    parser.add_argument("--use-chrome", action="store_true", help="使用本機 Chrome 瀏覽器（更能通過 Cloudflare 驗證）")
    parser.add_argument("--emails", type=Path, help="Path to .txt file with one email per line")
    parser.add_argument("--print-schedule", action="store_true")
    parser.add_argument("--scheduler", choices=["windows", "python"], default="windows")
    parser.add_argument("--create-windows-tasks", action="store_true")
    args = parser.parse_args(argv)
    return args


def main(argv: list[str] | None = None) -> int:
    args = build_args(argv)
    config, responses = load_responses(args.config, args.responses)

    if not args.form_url:
        args.form_url = (
            config.get("projectData", {}).get("surveyUrl")
            or config.get("surveyUrl")
            or (BASE_DIR / "mock_google_form.html").as_uri()
        )
    args.platform = detect_platform(args.form_url, args.platform)
    if not args.job_id:
        args.job_id = hashlib.sha1(args.form_url.encode("utf-8")).hexdigest()[:10]

    if args.daily_count and not args.days and not args.end_date:
        args.days = math.ceil(args.count / args.daily_count)

    if args.print_schedule:
        print_schedule(args)
        return 0
    if args.create_windows_tasks:
        create_windows_tasks(args)
        return 0

    options = RunOptions(
        form_url=args.form_url,
        platform=args.platform,
        count=args.count,
        headless=args.headless,
        submit=not args.no_submit,
        manual_submit=args.manual_submit,
        use_chrome=args.use_chrome,
        interval_min_sec=args.interval_min_sec,
        interval_max_sec=args.interval_max_sec,
        worker_index=args.worker_index,
        worker_total=args.worker_total,
        job_id=args.job_id,
        state_file=args.state_file,
        report_dir=args.report_dir,
    )
    # Build email list: file > auto-generate
    email_list: list[str] = []
    if args.emails:
        ep = resolve_path(args.emails)
        if ep.exists():
            email_list = [l.strip() for l in ep.read_text(encoding="utf-8").splitlines() if l.strip()]
            print(f"[Email] 讀取清單：{len(email_list)} 個（{'足夠' if len(email_list) >= args.count else '不足，將循環使用'}）")
        else:
            print(f"[警告] 找不到 Email 清單：{ep}，改用自動產生")
    if not email_list:
        email_list = [generate_email(i) for i in range(args.count)]
        print(f"[Email] 自動產生 {len(email_list)} 個模擬 Email（如需真實 Email 請用 --emails emails.txt）")
    # Inject unique email per submission index into responses list
    # (responses cycles; email must be per-index not per-response-slot)
    _email_by_index: dict[int, str] = {i: email_list[i % len(email_list)] for i in range(args.count)}

    rows = run_submissions(options, responses, _email_by_index)
    submitted = sum(1 for row in rows if row["status"] == "submitted")
    skipped = sum(1 for row in rows if row["status"] == "skipped_duplicate")
    failed = sum(1 for row in rows if row["status"] == "failed")
    print(f"SurveyAI runner finished: submitted={submitted}, skipped_duplicate={skipped}, failed={failed}")
    print(f"Report: {options.report_dir / (options.job_id + '_run_report.csv')}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
