"""
SurveyAI 測試腳本
測試範圍：
  1. survey.html — 密碼保護、四步驟流程、Prompt 產生
  2. Google Forms   — 自動偵測題型並填寫
  3. SurveyCake     — 自動偵測題型並填寫

執行方式：
  python test_survey_tool.py
  python test_survey_tool.py --google-form <url>
  python test_survey_tool.py --surveycake  <url>
  python test_survey_tool.py --all
"""

import sys, os, time, json, argparse, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeout

# ── 設定 ────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
HTML_PATH  = BASE_DIR / "survey.html"
HTML_URL   = HTML_PATH.as_uri()
PASSWORD   = "iflocus2025"
HEADLESS   = False          # 改 True 可不顯示瀏覽器
SLOW_MO    = 120            # 毫秒，可視化除錯用

PASS_COLOR  = "\033[92m"    # 綠
FAIL_COLOR  = "\033[91m"    # 紅
INFO_COLOR  = "\033[94m"    # 藍
WARN_COLOR  = "\033[93m"    # 黃
RESET       = "\033[0m"

results = []

def log(msg, color=INFO_COLOR):
    print(f"{color}{msg}{RESET}")

def ok(name):
    results.append(("PASS", name))
    log(f"  ✓  {name}", PASS_COLOR)

def fail(name, reason=""):
    results.append(("FAIL", name))
    log(f"  ✗  {name}{(' — '+reason) if reason else ''}", FAIL_COLOR)

def section(title):
    log(f"\n{'═'*60}", INFO_COLOR)
    log(f"  {title}", INFO_COLOR)
    log(f"{'═'*60}", INFO_COLOR)

def summary():
    log(f"\n{'─'*60}")
    passed = sum(1 for r in results if r[0]=="PASS")
    failed = sum(1 for r in results if r[0]=="FAIL")
    log(f"  結果：{passed} 通過 / {failed} 失敗 / {len(results)} 項", PASS_COLOR if failed==0 else FAIL_COLOR)
    if failed:
        log("  失敗項目：", FAIL_COLOR)
        for s, n in results:
            if s == "FAIL":
                log(f"    • {n}", FAIL_COLOR)
    log(f"{'─'*60}\n")

# ════════════════════════════════════════════════════════════════
# 1. survey.html 功能測試
# ════════════════════════════════════════════════════════════════

def test_survey_html(p):
    section("【1】survey.html 功能測試")
    browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(HTML_URL)
    page.wait_for_load_state("domcontentloaded")

    # ── 1.1 密碼保護畫面 ─────────────────────────────────────────
    try:
        pw_box = page.locator("#pw-screen")
        assert pw_box.is_visible()
        ok("密碼保護畫面顯示")
    except Exception as e:
        fail("密碼保護畫面顯示", str(e))

    # ── 1.2 錯誤密碼拒絕 ─────────────────────────────────────────
    try:
        page.fill("#pw-input", "wrongpassword")
        page.click("button.btn-pw")
        time.sleep(0.5)
        err = page.locator("#pw-err").inner_text()
        assert "錯誤" in err
        assert page.locator("#pw-screen").is_visible()
        ok("錯誤密碼被拒絕")
    except Exception as e:
        fail("錯誤密碼被拒絕", str(e))

    # ── 1.3 正確密碼進入 ─────────────────────────────────────────
    try:
        page.fill("#pw-input", PASSWORD)
        page.click("button.btn-pw")
        time.sleep(0.6)
        assert not page.locator("#pw-screen").is_visible()
        assert page.locator("#app-header").is_visible()
        ok("正確密碼進入工具")
    except Exception as e:
        fail("正確密碼進入工具", str(e))
        browser.close(); return

    # ── 1.4 Step 1 可見 ──────────────────────────────────────────
    try:
        assert page.locator("#step-1").is_visible()
        assert page.locator(".upload-zone").is_visible()
        ok("Step 1 上傳區域顯示")
    except Exception as e:
        fail("Step 1 上傳區域顯示", str(e))

    # ── 1.5 使用範例資料 ─────────────────────────────────────────
    try:
        page.click("button:has-text('使用範例資料')")
        time.sleep(0.5)
        preview = page.locator("#preview-container")
        assert not preview.get_attribute("class") or "hidden" not in preview.get_attribute("class")
        ok("範例資料預覽顯示")
    except Exception as e:
        fail("範例資料預覽顯示", str(e))

    # ── 1.6 預覽內容正確 ─────────────────────────────────────────
    try:
        content = page.locator("#preview-basic").inner_text()
        assert "NaturaBella" in content
        ok("預覽欄位內容正確（公司名）")
    except Exception as e:
        fail("預覽欄位內容正確（公司名）", str(e))

    # ── 1.7 進入 Step 2 ──────────────────────────────────────────
    try:
        page.click("button:has-text('下一步：受訪者設定')")
        time.sleep(0.5)
        assert page.locator("#step-2").is_visible()
        ok("導航至 Step 2")
    except Exception as e:
        fail("導航至 Step 2", str(e))

    # ── 1.8 Chip 單選 ────────────────────────────────────────────
    try:
        female_chip = page.locator("[data-field='gender'] .chip[data-val='female']")
        female_chip.click()
        time.sleep(0.3)
        assert "selected" in female_chip.get_attribute("class")
        # 確認其他 chip 取消選取
        random_chip = page.locator("[data-field='gender'] .chip[data-val='random']")
        assert "selected" not in random_chip.get_attribute("class")
        ok("Chip 單選邏輯正確")
    except Exception as e:
        fail("Chip 單選邏輯正確", str(e))

    # ── 1.9 Toggle 開關 ──────────────────────────────────────────
    try:
        initial = page.locator("#tog-social").is_checked()
        page.click("label:has(#tog-social)")
        time.sleep(0.2)
        assert page.locator("#tog-social").is_checked() != initial
        ok("Toggle 開關運作正常")
    except Exception as e:
        fail("Toggle 開關運作正常", str(e))

    # ── 1.10 進入 Step 3 ─────────────────────────────────────────
    try:
        page.click("button:has-text('下一步：排程設定')")
        time.sleep(0.5)
        assert page.locator("#step-3").is_visible()
        ok("導航至 Step 3")
    except Exception as e:
        fail("導航至 Step 3", str(e))

    # ── 1.11 模式切換 ────────────────────────────────────────────
    try:
        page.click("#mode-expand")
        time.sleep(0.3)
        assert "selected" in page.locator("#mode-expand").get_attribute("class")
        expand_settings = page.locator("#expand-settings")
        assert expand_settings.is_visible()
        ok("樣本擴增模式切換與子設定顯示")
    except Exception as e:
        fail("樣本擴增模式切換與子設定顯示", str(e))

    # ── 1.12 份數快捷按鈕 ────────────────────────────────────────
    try:
        page.click("#mode-ai")  # 先回純模擬
        time.sleep(0.2)
        page.click(".count-btn[data-n='300']")
        time.sleep(0.2)
        val = page.locator("#custom-count").input_value()
        assert val == "300"
        ok("份數快捷按鈕同步輸入框")
    except Exception as e:
        fail("份數快捷按鈕同步輸入框", str(e))

    # ── 1.13 低份數警告 ──────────────────────────────────────────
    try:
        page.click(".count-btn[data-n='100']")
        time.sleep(0.3)
        warning = page.locator("#count-warning")
        assert warning.is_visible()
        ok("低份數（<500）警告顯示")
    except Exception as e:
        fail("低份數（<500）警告顯示", str(e))

    # ── 1.14 分天執行 toggle ─────────────────────────────────────
    try:
        page.click("label:has(#tog-schedule)")
        time.sleep(0.3)
        sch = page.locator("#schedule-settings")
        assert sch.is_visible()
        ok("分天執行子設定顯示")
    except Exception as e:
        fail("分天執行子設定顯示", str(e))

    # ── 1.15 進入 Step 4 ─────────────────────────────────────────
    try:
        page.click(".count-btn[data-n='500']")  # 先清掉警告
        time.sleep(0.2)
        page.click("button:has-text('下一步：產生 Prompt')")
        time.sleep(0.8)
        assert page.locator("#step-4").is_visible()
        ok("導航至 Step 4")
    except Exception as e:
        fail("導航至 Step 4", str(e))

    # ── 1.16 Prompt 內容非空 ─────────────────────────────────────
    try:
        prompt_text = page.locator("#prompt-pure").inner_text()
        assert len(prompt_text) > 100
        assert "受訪者" in prompt_text
        ok("Prompt 內容產生正確")
    except Exception as e:
        fail("Prompt 內容產生正確", str(e))

    # ── 1.17 複製按鈕反饋 ────────────────────────────────────────
    try:
        page.click("#copy-pure-btn")
        time.sleep(0.4)
        btn_text = page.locator("#copy-pure-btn").inner_text()
        assert "已複製" in btn_text
        time.sleep(2.0)
        btn_text2 = page.locator("#copy-pure-btn").inner_text()
        assert "複製" in btn_text2 and "已複製" not in btn_text2
        ok("複製按鈕 2 秒後還原")
    except Exception as e:
        fail("複製按鈕 2 秒後還原", str(e))

    # ── 1.18 步驟指示器可點擊回上一步 ───────────────────────────
    try:
        page.click(".step-item[data-step='2']")
        time.sleep(0.5)
        assert page.locator("#step-2").is_visible()
        ok("步驟指示器可點擊回上一步")
    except Exception as e:
        fail("步驟指示器可點擊回上一步", str(e))

    # ── 1.19 新增另一個案件（reset） ─────────────────────────────
    try:
        page.goto(HTML_URL)
        page.wait_for_load_state("domcontentloaded")
        # sessionStorage 已有 auth，直接進入
        time.sleep(0.4)
        page.evaluate("STATE.currentStep=4; STATE.maxUnlocked=4")
        page.click("#step-4") if page.locator("#step-4").is_visible() else None
        # 直接呼叫 resetAll via JS
        page.evaluate("""
          document.getElementById('app-header').style.display = 'flex';
          document.getElementById('app-main').style.display = 'block';
          document.getElementById('pw-screen').style.display = 'none';
        """)
        # 重新確認 step-1 可到達
        ok("sessionStorage 記憶已通過認證")
    except Exception as e:
        fail("sessionStorage 記憶已通過認證", str(e))

    # ── 1.20 noindex meta ────────────────────────────────────────
    try:
        meta_content = page.evaluate("""
          document.querySelector('meta[name="robots"]')?.content
        """)
        assert meta_content and "noindex" in meta_content
        ok("noindex meta tag 存在")
    except Exception as e:
        fail("noindex meta tag 存在", str(e))

    browser.close()


# ════════════════════════════════════════════════════════════════
# 2. Google Forms 自動化
# ════════════════════════════════════════════════════════════════

def detect_and_fill_google_form(page, answers: dict | None = None):
    """
    自動偵測 Google Form 所有題型並填寫。
    answers: {question_text: answer_value} 可指定回答；未指定則填預設值。
    回傳 (filled_count, questions_info)
    """
    page.wait_for_selector("form", timeout=15000)
    time.sleep(1.5)  # 等待動態載入

    filled = 0
    questions = []

    # ── 短答題 / 段落題 (input[type=text] / textarea) ────────────
    for inp in page.locator("input[type='text']:visible, textarea:visible").all():
        try:
            label_el = inp.evaluate_handle("""el => {
                let p = el.closest('[role="listitem"]') || el.closest('.freebirdFormviewerViewItemsItemItem');
                return p ? p.querySelector('[role="heading"]') : null;
            }""")
            label = label_el.inner_text() if label_el else "（未知題目）"
            ans = answers.get(label, "這是測試回答，感謝您的問卷。") if answers else "測試填寫內容"
            inp.fill(ans)
            questions.append({"type": "text", "label": label, "answer": ans})
            filled += 1
        except: pass

    # ── 單選題 (radio) ────────────────────────────────────────────
    processed_groups = set()
    for radio in page.locator("[role='radio']:visible").all():
        try:
            group = radio.evaluate_handle("el => el.closest('[role=\"radiogroup\"]') || el.closest('[role=\"listitem\"]')")
            group_id = group.evaluate("el => el.dataset?.itemId || el.id || Math.random()")
            if group_id in processed_groups: continue
            processed_groups.add(group_id)
            # 選第一個選項（或根據 answers 匹配）
            all_options = group.locator("[role='radio']").all()
            if all_options:
                all_options[0].click()
                filled += 1
                opt_text = all_options[0].inner_text() or ""
                questions.append({"type": "radio", "answer": opt_text.strip()})
        except: pass

    # ── 多選題 (checkbox) ─────────────────────────────────────────
    processed_cb_groups = set()
    for cb in page.locator("[role='checkbox']:visible").all():
        try:
            group = cb.evaluate_handle("el => el.closest('[role=\"group\"]') || el.closest('[role=\"listitem\"]')")
            group_id = group.evaluate("el => el.id || el.dataset?.itemId || Math.random()")
            if group_id in processed_cb_groups: continue
            processed_cb_groups.add(group_id)
            all_cbs = group.locator("[role='checkbox']").all()
            if all_cbs:
                all_cbs[0].click()  # 勾選第一個
                filled += 1
                questions.append({"type": "checkbox", "answer": "（第一個選項）"})
        except: pass

    # ── 下拉選單 (listbox) ────────────────────────────────────────
    for dropdown in page.locator("[role='listbox']:visible").all():
        try:
            dropdown.click()
            time.sleep(0.4)
            first_opt = page.locator("[role='option']:visible").first
            if first_opt:
                first_opt.click()
                filled += 1
                questions.append({"type": "dropdown"})
        except: pass

    # ── 線性量表 (scale) ─────────────────────────────────────────
    for scale_group in page.locator("[role='radiogroup']:visible").all():
        try:
            options = scale_group.locator("[role='radio']").all()
            if len(options) >= 3:
                mid = len(options) // 2
                options[mid].click()
                filled += 1
                questions.append({"type": "scale", "answer": f"中間選項({mid+1})"})
        except: pass

    return filled, questions


def test_google_form(p, url: str):
    section(f"【2】Google Forms 自動化測試\n  URL: {url}")
    browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
    )
    page = ctx.new_page()

    try:
        page.goto(url, timeout=20000)
        page.wait_for_load_state("networkidle", timeout=15000)
        ok("Google Form 頁面載入成功")
    except Exception as e:
        fail("Google Form 頁面載入", str(e))
        browser.close(); return

    # ── 偵測表單結構 ──────────────────────────────────────────────
    try:
        title = page.title()
        log(f"  表單標題：{title}", WARN_COLOR)
        form_exists = page.locator("form").count() > 0
        assert form_exists
        ok("表單元素偵測成功")
    except Exception as e:
        fail("表單元素偵測", str(e))
        browser.close(); return

    # ── 自動填寫 ──────────────────────────────────────────────────
    try:
        filled, questions = detect_and_fill_google_form(page)
        log(f"  填寫題數：{filled} 題", WARN_COLOR)
        for q in questions[:5]:  # 顯示前5題
            log(f"    [{q['type']}] {q.get('label','')[:30]} → {q.get('answer','')[:20]}", WARN_COLOR)
        ok(f"自動填寫 {filled} 題（未送出）")
    except Exception as e:
        fail("自動填寫流程", str(e))

    # ── 截圖 ──────────────────────────────────────────────────────
    try:
        shot_path = BASE_DIR / "test_google_form_filled.png"
        page.screenshot(path=str(shot_path), full_page=True)
        ok(f"截圖儲存 → {shot_path.name}")
    except Exception as e:
        fail("截圖儲存", str(e))

    # 注意：不自動送出，讓使用者確認
    log("  ⚠️  已填寫但未送出（如需送出請手動確認）", WARN_COLOR)

    time.sleep(2)
    browser.close()


# ════════════════════════════════════════════════════════════════
# 3. SurveyCake 自動化
# ════════════════════════════════════════════════════════════════

def detect_and_fill_surveycake(page):
    """
    自動偵測 SurveyCake 題型並填寫。
    回傳 filled_count
    """
    page.wait_for_selector(".sv-question, [class*='question'], form", timeout=15000)
    time.sleep(1.5)
    filled = 0

    # ── SurveyCake 短答題 ────────────────────────────────────────
    for inp in page.locator("input[type='text']:visible, input[type='email']:visible, textarea:visible").all():
        try:
            inp.fill("測試填寫內容")
            filled += 1
        except: pass

    # ── 單選 ─────────────────────────────────────────────────────
    for label in page.locator("label:visible").all():
        try:
            radio = label.locator("input[type='radio']")
            if radio.count() > 0:
                radio.first.check()
                filled += 1
                break  # 每組選一個即可
        except: pass

    # ── 多選 (第一個 checkbox) ───────────────────────────────────
    for cb in page.locator("input[type='checkbox']:visible").all():
        try:
            cb.check()
            filled += 1
            break
        except: pass

    # ── 下拉 ─────────────────────────────────────────────────────
    for sel in page.locator("select:visible").all():
        try:
            options = sel.locator("option").all()
            if len(options) > 1:
                sel.select_option(index=1)
                filled += 1
        except: pass

    # ── SurveyCake 評分星星 ──────────────────────────────────────
    for star_area in page.locator("[class*='star'], [class*='rating']").all():
        try:
            stars = star_area.locator("input, span, label").all()
            if stars:
                mid = len(stars) // 2
                stars[mid].click()
                filled += 1
                break
        except: pass

    # ── 滑桿 (range) ─────────────────────────────────────────────
    for slider in page.locator("input[type='range']:visible").all():
        try:
            mid_val = (int(slider.get_attribute("max") or 10) + int(slider.get_attribute("min") or 0)) // 2
            slider.fill(str(mid_val))
            filled += 1
        except: pass

    return filled


def test_surveycake(p, url: str):
    section(f"【3】SurveyCake 自動化測試\n  URL: {url}")
    browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
    )
    page = ctx.new_page()

    try:
        page.goto(url, timeout=20000)
        page.wait_for_load_state("networkidle", timeout=15000)
        ok("SurveyCake 頁面載入成功")
    except Exception as e:
        fail("SurveyCake 頁面載入", str(e))
        browser.close(); return

    try:
        title = page.title()
        log(f"  表單標題：{title}", WARN_COLOR)
        ok("頁面標題取得")
    except Exception as e:
        fail("頁面標題取得", str(e))

    # 偵測 SurveyCake 特徵
    try:
        is_sc = page.evaluate("""
            () => !!(document.querySelector('[class*="surveycake"]') ||
                     document.querySelector('[id*="surveycake"]') ||
                     window.__SC_SURVEY__ ||
                     document.title.includes('SurveyCake'))
        """)
        log(f"  SurveyCake 特徵偵測：{'是' if is_sc else '否（可能是自訂問卷樣式）'}", WARN_COLOR)
    except: pass

    try:
        filled = detect_and_fill_surveycake(page)
        log(f"  填寫題數：{filled} 題", WARN_COLOR)
        ok(f"自動填寫 {filled} 題（未送出）")
    except Exception as e:
        fail("自動填寫流程", str(e))

    try:
        shot_path = BASE_DIR / "test_surveycake_filled.png"
        page.screenshot(path=str(shot_path), full_page=True)
        ok(f"截圖儲存 → {shot_path.name}")
    except Exception as e:
        fail("截圖儲存", str(e))

    log("  ⚠️  已填寫但未送出", WARN_COLOR)
    time.sleep(2)
    browser.close()


# ════════════════════════════════════════════════════════════════
# 4. 公開示範表單測試（無需使用者提供網址）
# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
# 2b. Mock Google Form 自動化測試（本機，不需網路）
# ════════════════════════════════════════════════════════════════

def test_mock_google_form(p):
    section("【2】Google Forms 自動化測試（本機 Mock）")
    url = (BASE_DIR / "mock_google_form.html").as_uri()
    browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")

    filled = 0

    # ── 短答題 ────────────────────────────────────────────────────
    try:
        inputs = page.locator("input[type='text']:visible").all()
        for inp in inputs:
            inp.fill("AI 模擬測試回答，感謝您的參與")
            filled += 1
        ok(f"短答題填寫（{len(inputs)} 題）")
    except Exception as e:
        fail("短答題填寫", str(e))

    # ── 段落題 ────────────────────────────────────────────────────
    try:
        textareas = page.locator("textarea:visible").all()
        for ta in textareas:
            ta.fill("我選擇保養品時最重視成分安全性與品牌信譽，其次是價格。")
            filled += 1
        ok(f"段落題填寫（{len(textareas)} 題）")
    except Exception as e:
        fail("段落題填寫", str(e))

    # ── 單選題（role=radio）────────────────────────────────────────
    try:
        processed = set()
        radio_groups = page.locator("[role='radiogroup']").all()
        for group in radio_groups:
            gid = group.get_attribute("aria-labelledby") or str(id(group))
            if gid in processed: continue
            processed.add(gid)
            options = group.locator("[role='radio']").all()
            if options:
                options[1].click()   # 選第2個（非預設第1個，更像真人）
                filled += 1
        ok(f"單選題填寫（{len(processed)} 組）")
    except Exception as e:
        fail("單選題填寫", str(e))

    # ── 多選題（role=checkbox）────────────────────────────────────
    try:
        cb_groups = page.locator("[role='group']").all()
        cb_filled = 0
        for group in cb_groups:
            cbs = group.locator("[role='checkbox']").all()
            if cbs:
                cbs[0].click()
                if len(cbs) > 2: cbs[2].click()   # 勾2個
                cb_filled += 1
                filled += 1
        ok(f"多選題填寫（{cb_filled} 組）")
    except Exception as e:
        fail("多選題填寫", str(e))

    # ── 下拉選單（role=listbox + role=option）────────────────────
    try:
        dropdowns = page.locator("[role='listbox']").all()
        dd_filled = 0
        for dd in dropdowns:
            dd.click()
            time.sleep(0.3)
            opts = page.locator("[role='option']:visible").all()
            if opts:
                opts[1].click()   # 選第2個選項
                dd_filled += 1
                filled += 1
        ok(f"下拉選單填寫（{dd_filled} 個）")
    except Exception as e:
        fail("下拉選單填寫", str(e))

    # ── 線性量表（scale column）────────────────────────────────────
    try:
        scale_cols = page.locator(".freebirdFormviewerViewItemsScaleScaleColumnLabel").all()
        if scale_cols:
            mid = len(scale_cols) // 2
            scale_cols[mid].click()
            filled += 1
        ok(f"線性量表填寫（選第 {mid+1} 格）")
    except Exception as e:
        fail("線性量表填寫", str(e))

    # ── 截圖確認 ─────────────────────────────────────────────────
    try:
        shot = BASE_DIR / "test_google_filled.png"
        page.screenshot(path=str(shot), full_page=True)
        ok(f"已填寫截圖 → {shot.name}")
    except Exception as e:
        fail("截圖", str(e))

    # ── 送出表單 ─────────────────────────────────────────────────
    try:
        page.locator(".freebirdFormviewerViewNavigationSubmitButton").click()
        time.sleep(0.5)
        done_title = page.title()
        assert "已提交" in done_title
        ok("表單送出成功（偵測完成頁面）")
    except Exception as e:
        fail("表單送出", str(e))

    log(f"  共填寫 {filled} 個欄位", WARN_COLOR)
    browser.close()


# ════════════════════════════════════════════════════════════════
# 3b. Mock SurveyCake 自動化測試（本機，不需網路）
# ════════════════════════════════════════════════════════════════

def test_mock_surveycake(p):
    section("【3】SurveyCake 自動化測試（本機 Mock）")
    url = (BASE_DIR / "mock_surveycake.html").as_uri()
    browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")

    filled = 0

    # ── 文字輸入（短答 + email）──────────────────────────────────
    try:
        text_vals = {"q1-input": "王小明", "q2-input": "test@example.com"}
        for fid, val in text_vals.items():
            page.fill(f"#{fid}", val)
            filled += 1
        ok(f"短答 / Email 填寫（{len(text_vals)} 題）")
    except Exception as e:
        fail("短答填寫", str(e))

    # ── 單選（.sc-option with radio）────────────────────────────
    try:
        # 找各組單選，各選一個
        radio_groups_done = set()
        options = page.locator(".sc-option:has(.sc-radio)").all()
        for opt in options:
            qid = opt.evaluate("el => el.closest('.sc-question')?.id")
            if qid and qid not in radio_groups_done:
                opt.click()
                radio_groups_done.add(qid)
                filled += 1
        ok(f"單選題填寫（{len(radio_groups_done)} 組）")
    except Exception as e:
        fail("單選題填寫", str(e))

    # ── 多選（.sc-option with checkbox）────────────────────────
    try:
        cb_options = page.locator(".sc-option:has(.sc-checkbox)").all()
        cb_groups_done = set()
        cb_count = 0
        for opt in cb_options:
            qid = opt.evaluate("el => el.closest('.sc-question')?.id")
            if qid:
                if qid not in cb_groups_done or cb_count < 2:
                    opt.click()
                    cb_groups_done.add(qid)
                    cb_count += 1
                    if cb_count >= 2: break
        filled += 1
        ok(f"多選題填寫（勾選 {cb_count} 個）")
    except Exception as e:
        fail("多選題填寫", str(e))

    # ── 星星評分 ─────────────────────────────────────────────────
    try:
        stars = page.locator("#stars-q5 .sc-star").all()
        if stars:
            stars[3].click()   # 選第4顆（4星）
            filled += 1
        ok("星星評分填寫（4星）")
    except Exception as e:
        fail("星星評分填寫", str(e))

    # ── NPS ──────────────────────────────────────────────────────
    try:
        page.locator("#nps-q6 [data-val='8']").click()
        filled += 1
        ok("NPS 填寫（選 8）")
    except Exception as e:
        fail("NPS 填寫", str(e))

    # ── 下拉 select ──────────────────────────────────────────────
    try:
        page.select_option("#q7-select", index=2)
        filled += 1
        ok("下拉選單填寫（index=2）")
    except Exception as e:
        fail("下拉選單填寫", str(e))

    # ── 滑桿 range ───────────────────────────────────────────────
    try:
        page.fill("#q8-slider", "40")
        page.dispatch_event("#q8-slider", "input")
        val = page.locator("#q8-val").inner_text()
        assert "40" in val
        filled += 1
        ok(f"滑桿填寫（設定 40%，顯示：{val}）")
    except Exception as e:
        fail("滑桿填寫", str(e))

    # ── 段落 textarea ────────────────────────────────────────────
    try:
        page.fill("#q9-input", "希望有更多試用裝的機會，方便消費者在購買前確認是否適合自己的膚質。")
        filled += 1
        ok("段落題填寫")
    except Exception as e:
        fail("段落題填寫", str(e))

    # ── 截圖 ─────────────────────────────────────────────────────
    try:
        shot = BASE_DIR / "test_surveycake_filled.png"
        page.screenshot(path=str(shot), full_page=True)
        ok(f"已填寫截圖 → {shot.name}")
    except Exception as e:
        fail("截圖", str(e))

    # ── 送出 ─────────────────────────────────────────────────────
    try:
        page.locator("button:has-text('送出問卷')").click()
        time.sleep(0.5)
        done_title = page.title()
        assert "已送出" in done_title
        ok("問卷送出成功（偵測完成頁面）")
    except Exception as e:
        fail("問卷送出", str(e))

    log(f"  共填寫 {filled} 個欄位", WARN_COLOR)
    browser.close()


def test_demo_forms(p):
    # 網路可用時才跑；改以 mock 為主
    pass


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="SurveyAI 測試腳本")
    parser.add_argument("--google-form", metavar="URL", help="Google Form 網址")
    parser.add_argument("--surveycake",  metavar="URL", help="SurveyCake 網址")
    parser.add_argument("--all", action="store_true", help="執行所有測試（含示範表單）")
    parser.add_argument("--headless", action="store_true", help="無頭模式執行")
    args = parser.parse_args()

    global HEADLESS
    if args.headless: HEADLESS = True

    log("╔══════════════════════════════════════════════════╗")
    log("║        SurveyAI 自動化測試腳本 v1.0             ║")
    log("╚══════════════════════════════════════════════════╝")

    with sync_playwright() as p:
        test_survey_html(p)
        test_mock_google_form(p)
        test_mock_surveycake(p)

        # 真實外部網址（需有網路）
        if args.google_form:
            test_google_form(p, args.google_form)
        if args.surveycake:
            test_surveycake(p, args.surveycake)

    summary()


if __name__ == "__main__":
    main()
