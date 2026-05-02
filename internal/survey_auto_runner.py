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


DEFAULT_RESPONSES = [
    {
        "name": "Respondent A",
        "email": "respondent.a@example.com",
        "short_text": "I usually discover products from social platforms.",
        "long_text": "Ingredient safety, reviews, and price are the main reasons I decide to try a product.",
        "radio": "25-34",
        "checkbox": "ig",
        "select": "500-1000",
        "rating": "4",
        "nps": "8",
        "slider": "45",
    },
    {
        "name": "Respondent B",
        "email": "respondent.b@example.com",
        "short_text": "Friends and review sites influence my purchase decisions.",
        "long_text": "I prefer products with clear labels, reliable customer support, and trial-size options.",
        "radio": "35-44",
        "checkbox": "review",
        "select": "1000-2000",
        "rating": "5",
        "nps": "9",
        "slider": "55",
    },
    {
        "name": "Respondent C",
        "email": "respondent.c@example.com",
        "short_text": "I compare several brands before buying.",
        "long_text": "A brand feels trustworthy when the benefits, ingredients, and real user feedback are consistent.",
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
    values = [
        row.get("short_text") or row.get("name") or "SurveyAI test response",
        row.get("long_text") or row.get("reason") or "This is an automated test response.",
        row.get("email") or "respondent@example.com",
    ]
    filled = 0
    fields = page.locator("input[type='text']:visible, input[type='email']:visible, textarea:visible").all()
    for idx, field in enumerate(fields):
        field.fill(str(values[min(idx, len(values) - 1)]))
        filled += 1
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


def fill_surveycake(page: Page, row: dict[str, Any], submit: bool) -> dict[str, Any]:
    page.wait_for_selector("body", timeout=15000)
    filled = fill_first_text_fields(page, row)

    questions = page.locator(".sc-question, [class*='question']").all()
    for question in questions:
        options = question.locator(".sc-option:visible")
        if options.count():
            wanted = row.get("radio") or row.get("checkbox")
            if click_option_by_value(options, wanted, fallback_index=0):
                filled += 1

        select = question.locator("select:visible")
        if select.count():
            value = str(row.get("select") or "")
            try:
                select.first.select_option(value=value)
            except Exception:
                select.first.select_option(index=1)
            filled += 1

    stars = page.locator(".sc-star:visible")
    if stars.count():
        rating = int(row.get("rating") or 4)
        stars.nth(max(0, min(rating - 1, stars.count() - 1))).click()
        filled += 1

    nps = page.locator(".sc-nps-btn:visible")
    if nps.count():
        score = int(row.get("nps") or 8)
        target = page.locator(f".sc-nps-btn[data-val='{score}']")
        (target.first if target.count() else nps.nth(min(score, nps.count() - 1))).click()
        filled += 1

    sliders = page.locator("input[type='range']:visible").all()
    for slider in sliders:
        slider.fill(str(row.get("slider") or 50))
        filled += 1

    submitted = False
    if submit:
        page.locator(".sc-btn-primary:visible, button:has-text('送出'), button:has-text('Submit')").first.click()
        submitted = wait_for_success(page, ["#sc-done", "SurveyCake Mock"])

    return {"filled": filled, "submitted": submitted}


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


def run_submissions(options: RunOptions, responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state = load_state(options.state_file)
    submitted_keys = set(state.get("submitted", []))
    indices = list(slice_for_worker(options.count, options.worker_index, options.worker_total))
    results: list[dict[str, Any]] = []
    options.report_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=options.headless)
        for local_no, response_index in enumerate(indices, start=1):
            key = submission_key(options.job_id, options.worker_index, response_index)
            if key in submitted_keys:
                results.append({"response_index": response_index + 1, "status": "skipped_duplicate"})
                continue

            context = browser.new_context(locale="zh-TW", timezone_id="Asia/Taipei")
            page = context.new_page()
            row = response_for_index(responses, response_index)
            started = datetime.now()
            status = "failed"
            detail: dict[str, Any] = {}
            try:
                page.goto(options.form_url, wait_until="domcontentloaded", timeout=30000)
                if options.platform == "surveycake":
                    detail = fill_surveycake(page, row, options.submit)
                else:
                    detail = fill_google(page, row, options.submit)

                if not options.submit or detail.get("submitted"):
                    status = "submitted" if options.submit else "filled_no_submit"
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
                context.close()

            results.append(
                {
                    "response_index": response_index + 1,
                    "worker_index": options.worker_index,
                    "status": status,
                    "filled": detail.get("filled", 0),
                    "submitted": detail.get("submitted", False),
                    "seconds": round((datetime.now() - started).total_seconds(), 2),
                    "screenshot": screenshot.name,
                    "error": detail.get("error", ""),
                }
            )

            if local_no < len(indices):
                pause = random.uniform(options.interval_min_sec, options.interval_max_sec)
                if pause > 0:
                    time.sleep(pause)
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
        interval_min_sec=args.interval_min_sec,
        interval_max_sec=args.interval_max_sec,
        worker_index=args.worker_index,
        worker_total=args.worker_total,
        job_id=args.job_id,
        state_file=args.state_file,
        report_dir=args.report_dir,
    )
    rows = run_submissions(options, responses)
    submitted = sum(1 for row in rows if row["status"] == "submitted")
    skipped = sum(1 for row in rows if row["status"] == "skipped_duplicate")
    failed = sum(1 for row in rows if row["status"] == "failed")
    print(f"SurveyAI runner finished: submitted={submitted}, skipped_duplicate={skipped}, failed={failed}")
    print(f"Report: {options.report_dir / (options.job_id + '_run_report.csv')}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
