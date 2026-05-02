import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
import sys


BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

import survey_auto_runner as runner


class SurveyAutoRunnerTests(unittest.TestCase):
    def run_mock(self, filename: str, platform: str, count: int = 2):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args = runner.build_args(
                [
                    "--form-url",
                    (BASE_DIR / filename).as_uri(),
                    "--platform",
                    platform,
                    "--count",
                    str(count),
                    "--headless",
                    "--interval-min-sec",
                    "0",
                    "--interval-max-sec",
                    "0",
                    "--job-id",
                    f"test_{platform}",
                    "--state-file",
                    str(tmp_path / "state.json"),
                    "--report-dir",
                    str(tmp_path / "reports"),
                ]
            )
            config, responses = runner.load_responses(args.config, args.responses)
            options = runner.RunOptions(
                form_url=args.form_url,
                platform=runner.detect_platform(args.form_url, args.platform),
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
            first = runner.run_submissions(options, responses)
            second = runner.run_submissions(options, responses)
            state = runner.load_state(args.state_file)
            return first, second, state

    def test_google_mock_fills_and_submits_once(self):
        first, second, state = self.run_mock("mock_google_form.html", "google", count=2)

        self.assertEqual([row["status"] for row in first], ["submitted", "submitted"])
        self.assertTrue(all(row["filled"] >= 5 for row in first))
        self.assertEqual([row["status"] for row in second], ["skipped_duplicate", "skipped_duplicate"])
        self.assertEqual(len(state["submitted"]), 2)

    def test_surveycake_mock_fills_and_submits_once(self):
        first, second, state = self.run_mock("mock_surveycake.html", "surveycake", count=2)

        self.assertEqual([row["status"] for row in first], ["submitted", "submitted"])
        self.assertTrue(all(row["filled"] >= 7 for row in first))
        self.assertEqual([row["status"] for row in second], ["skipped_duplicate", "skipped_duplicate"])
        self.assertEqual(len(state["submitted"]), 2)

    def test_worker_split_does_not_overlap(self):
        self.assertEqual(list(runner.slice_for_worker(10, 1, 3)), [0, 1, 2])
        self.assertEqual(list(runner.slice_for_worker(10, 2, 3)), [3, 4, 5])
        self.assertEqual(list(runner.slice_for_worker(10, 3, 3)), [6, 7, 8, 9])

    def test_schedule_prints_windows_tasks(self):
        args = runner.build_args(
            [
                "--form-url",
                "https://forms.gle/example",
                "--count",
                "7",
                "--daily-count",
                "3",
                "--start-date",
                "2026-05-04",
                "--print-schedule",
                "--job-id",
                "case123",
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            runner.print_schedule(args)
        out = buf.getvalue()

        self.assertIn("must stay powered on, awake, online", out)
        self.assertIn('schtasks /Create /TN "SurveyAI_case123_day1"', out)
        self.assertIn("--count 3", out)
        self.assertIn('schtasks /Create /TN "SurveyAI_case123_day3"', out)
        self.assertIn("--count 1", out)


if __name__ == "__main__":
    unittest.main()
