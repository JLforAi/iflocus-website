# SurveyAI GitHub Actions 排程方案

這是「執行端電腦不用開機」的 optional 方案。它使用 GitHub Actions 的 `schedule` 在雲端 Ubuntu runner 執行 `internal/survey_auto_runner.py`。

## 啟用方式

到 GitHub repo `Settings -> Secrets and variables -> Actions` 設定：

Secrets:

- `SURVEY_FORM_URL`: 真實 Google Forms 或 SurveyCake 問卷網址

Variables:

- `SURVEY_AUTO_ENABLED`: 設為 `true` 才會讓每日排程真的執行
- `SURVEY_PLATFORM`: `auto`、`google` 或 `surveycake`，預設可用 `auto`
- `SURVEY_COUNT_PER_RUN`: 每次 GitHub 排程要送出的份數，例如 `10`
- `SURVEY_INTERVAL_MIN_SEC`: 每份之間最短間隔秒數，例如 `30`
- `SURVEY_INTERVAL_MAX_SEC`: 每份之間最長間隔秒數，例如 `90`

Workflow 檔案：`.github/workflows/survey-auto-runner.yml`

預設 cron 是每天 UTC 01:17，也就是台灣時間 09:17。

## 手動測試

到 GitHub repo 的 `Actions -> SurveyAI Cloud Schedule -> Run workflow`：

1. `enabled` 輸入 `true`
2. 可填 `form_url` 覆蓋 secret
3. `count` 先用 `1` 或 `2`
4. 確認表單後台有收到資料，再調高份數

## 重要限制

- GitHub runner 的 IP 不是一般消費者網路，Google Forms / SurveyCake 可能更容易觸發風控或驗證。
- GitHub Actions 的排程不是精準到秒，尖峰時段可能延遲數分鐘以上。
- 免費額度和單次 job 執行時間有限，不適合一次送大量份數。
- 每次 workflow 是新的雲端機器；跨天總量控管建議靠 `SURVEY_COUNT_PER_RUN` 和啟停 `SURVEY_AUTO_ENABLED` 控制。
- 不要把問卷網址、帳密、API key 寫死在 Python 檔，請使用 GitHub Secrets / Variables。

## 建議用法

本機方案適合需要多人分工、模擬較自然節奏、或需要使用特定網路環境的專案。

GitHub Actions 方案適合少量、固定時間、自動化測試或內部 mock 驗證。若要用在正式問卷，建議先用 `count=1` 手動測試，再逐步調整。
