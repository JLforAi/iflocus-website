"""
iFLocus internal Clicks QA runner.

Purpose:
- Schedule authorized page visits / optional selector clicks for owned QA pages.
- Produce CSV reports and screenshots through GitHub Actions or local runs.

This runner is intentionally allowlist-based. It is not a traffic inflation tool.

Examples:
  python -X utf8 internal/clicks_runner.py --url https://iflocus.com/ --count 3 --dry-run
  python -X utf8 internal/clicks_runner.py --url https://iflocus.com/internal/survey.html --count 2 --headless
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, time as dt_time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeout, sync_playwright


BASE_DIR = Path(__file__).parent
DEFAULT_REPORT_DIR = BASE_DIR / "clicks_results"
DEFAULT_ALLOWED_HOSTS = [
    "iflocus.com",
    "www.iflocus.com",
    "dailynowbuzz.com",
    "www.dailynowbuzz.com",
    "localhost",
    "127.0.0.1",
]


@dataclass
class ClickOptions:
    url: str
    count: int
    selector: str
    start_hour: int
    end_hour: int
    interval_min_sec: float
    interval_max_sec: float
    headless: bool
    dry_run: bool
    allowed_hosts: list[str]
    report_dir: Path
    job_id: str


def parse_allowed_hosts(value: str) -> list[str]:
    hosts = [item.strip().lower() for item in value.split(",") if item.strip()]
    return hosts or DEFAULT_ALLOWED_HOSTS


def assert_allowed_url(url: str, allowed_hosts: list[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are supported.")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL host is missing.")
    for allowed in allowed_hosts:
        if host == allowed or host.endswith("." + allowed):
            return
    allowed_text = ", ".join(allowed_hosts)
    raise ValueError(f"URL host '{host}' is not allowlisted. Allowed hosts: {allowed_text}")


def within_time_window(now: datetime, start_hour: int, end_hour: int) -> bool:
    current = now.time()
    start = dt_time(start_hour, 0)
    end = dt_time(end_hour, 59, 59)
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def run_clicks(options: ClickOptions) -> list[dict[str, str]]:
    assert_allowed_url(options.url, options.allowed_hosts)
    options.report_dir.mkdir(parents=True, exist_ok=True)

    if not within_time_window(datetime.now(), options.start_hour, options.end_hour):
        row = {
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "url": options.url,
            "status": "skipped_outside_time_window",
            "http_status": "",
            "title": "",
            "selector": options.selector,
            "screenshot": "",
            "error": f"Allowed window is {options.start_hour}:00-{options.end_hour}:59",
        }
        write_report(options, [row])
        return [row]

    if options.dry_run:
        rows = [
            {
                "run_at": datetime.now().isoformat(timespec="seconds"),
                "url": options.url,
                "status": "dry_run",
                "http_status": "",
                "title": "",
                "selector": options.selector,
                "screenshot": "",
                "error": "",
            }
            for _ in range(options.count)
        ]
        write_report(options, rows)
        return rows

    rows: list[dict[str, str]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=options.headless)
        for idx in range(1, options.count + 1):
            context = browser.new_context(locale="zh-TW", timezone_id="Asia/Taipei")
            page = context.new_page()
            status = "failed"
            http_status = ""
            title = ""
            screenshot_name = ""
            error = ""
            try:
                response = page.goto(options.url, wait_until="domcontentloaded", timeout=30000)
                http_status = str(response.status) if response else ""
                page.wait_for_load_state("networkidle", timeout=10000)
                title = page.title()

                if options.selector:
                    target = page.locator(options.selector).first
                    target.wait_for(state="visible", timeout=10000)
                    target.click()
                    status = "selector_clicked"
                else:
                    status = "visited"

                screenshot_name = f"{options.job_id}_{idx:03d}.png"
                page.screenshot(path=str(options.report_dir / screenshot_name), full_page=True)
            except PlaywrightTimeout as exc:
                error = f"timeout: {exc}"
            except Exception as exc:
                error = str(exc)
            finally:
                context.close()

            rows.append(
                {
                    "run_at": datetime.now().isoformat(timespec="seconds"),
                    "url": options.url,
                    "status": status,
                    "http_status": http_status,
                    "title": title,
                    "selector": options.selector,
                    "screenshot": screenshot_name,
                    "error": error[:500],
                }
            )

            if idx < options.count:
                time.sleep(random.uniform(options.interval_min_sec, options.interval_max_sec))
        browser.close()

    write_report(options, rows)
    return rows


def write_report(options: ClickOptions, rows: list[dict[str, str]]) -> Path:
    report_path = options.report_dir / f"{options.job_id}_clicks_report.csv"
    if not rows:
        report_path.write_text("", encoding="utf-8")
        return report_path
    with report_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    meta_path = options.report_dir / f"{options.job_id}_clicks_config.json"
    meta_path.write_text(
        json.dumps(
            {
                "url": options.url,
                "count": options.count,
                "selector": options.selector,
                "startHour": options.start_hour,
                "endHour": options.end_hour,
                "intervalMinSec": options.interval_min_sec,
                "intervalMaxSec": options.interval_max_sec,
                "allowedHosts": options.allowed_hosts,
                "jobId": options.job_id,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return report_path


def build_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="iFLocus Clicks QA runner")
    parser.add_argument("--url", required=True, help="Owned or authorized URL to visit")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--selector", default="", help="Optional CSS selector to click after page load")
    parser.add_argument("--start-hour", type=int, default=9)
    parser.add_argument("--end-hour", type=int, default=22)
    parser.add_argument("--interval-min-sec", type=float, default=30)
    parser.add_argument("--interval-max-sec", type=float, default=90)
    parser.add_argument("--allowed-hosts", default=",".join(DEFAULT_ALLOWED_HOSTS))
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--job-id", default="")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = build_args(argv)
    if args.count < 1:
        raise ValueError("--count must be at least 1")
    if not 0 <= args.start_hour <= 23 or not 0 <= args.end_hour <= 23:
        raise ValueError("--start-hour and --end-hour must be between 0 and 23")
    if args.interval_max_sec < args.interval_min_sec:
        raise ValueError("--interval-max-sec must be >= --interval-min-sec")

    job_id = args.job_id or "clicks-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    options = ClickOptions(
        url=args.url,
        count=args.count,
        selector=args.selector.strip(),
        start_hour=args.start_hour,
        end_hour=args.end_hour,
        interval_min_sec=args.interval_min_sec,
        interval_max_sec=args.interval_max_sec,
        headless=args.headless,
        dry_run=args.dry_run,
        allowed_hosts=parse_allowed_hosts(args.allowed_hosts),
        report_dir=args.report_dir,
        job_id=job_id,
    )
    rows = run_clicks(options)
    ok = sum(1 for row in rows if row["status"] in ("visited", "selector_clicked", "dry_run"))
    skipped = sum(1 for row in rows if row["status"].startswith("skipped"))
    failed = len(rows) - ok - skipped
    print(f"Clicks QA finished: ok={ok}, skipped={skipped}, failed={failed}")
    print(f"Report: {options.report_dir / (options.job_id + '_clicks_report.csv')}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
