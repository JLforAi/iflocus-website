# FB Integration — 7/1 Launch Prep SUMMARY

> Branch: `feature/fb-integration`
> Base: `main` @ c788f19
> Date: 2026-06-01
> Scope: tasks 1–6 implemented; task 7 (cleanup) is a **review list only**, nothing deleted yet.
>
> ⚠️ This file overwrites a prior SUMMARY for the `content-review-fixes` branch. If that history is still needed, recover from git: `git log -- SUMMARY.md`.

---

## 1. Commits on this branch

| # | SHA (short) | Type | What |
|---|---|---|---|
| 1 | 8cd7b91 | feat(fb) | Footer FB upgrade + homepage CTA strip + contact-page dual-button block (HTML) |
| 2 | 154de76 | style(fb) | CSS for all FB components (split from #1 because pre-existing un-staged `style.css` tweaks needed to stay separate) |
| 3 | 805fd0d | feat(video) | OMO page video grid + 4 placeholders |
| 4 | a4a56a4 | feat(video) | Sports-marketing page video grid + 4 placeholders |
| 5 | bc39178 | feat(video) | Fill OMO + sports placeholders with real FB embeds + add `.fb-video-cta-card` variant for "more videos" slots |

Task 7 cleanup commit is **not** made yet — awaiting Joseph's confirmation on the list below.

## 2. Files modified

| File | Change |
|---|---|
| [js/components.js](js/components.js) | Footer FB list-item upgraded from plain text to icon + label「追蹤 iFLocus 粉絲團」. Single source of truth → propagates site-wide. No second FB entry added, per追加要求. |
| [index.html](index.html) | New `.fb-follow-strip` section inserted between the FAQ section and the final CTA. |
| [contact_us.html](contact_us.html) | New `.fb-dual-section` directly under the hero with two buttons (FB fanpage + Messenger). The old「FB Messenger」聯絡資訊小卡 removed to avoid duplication. |
| [iflocus.html](iflocus.html) | New `.fb-video-section` (titled「OMO 整合行銷 影音案例」) inserted between the existing image content and the bottom CTA. |
| [sports-marketing.html](sports-marketing.html) | Same video section, titled「運動行銷 影音案例」, before the bottom CTA. |
| [css/style.css](css/style.css) | +153 lines appended for `.footer-fb-link`, `.fb-follow-strip`, `.fb-dual-section`, `.fb-video-*` plus one combined `@media(max-width:768px)` block. |

## 3. Video slots — final state

Updated after the FB embed sweep that started at `bc39178` and finalised at `b565682` (and the slot-1 rollback that supersedes it).

### iFLocus OMO (`iflocus.html`) — 3 videos + 1 featured CTA + 1 generic CTA? No, exactly 4 cells:

| Slot | Content | Source / target |
|---|---|---|
| 1 | iframe | `facebook.com/reel/1537253340875553/` |
| 2 | iframe | `facebook.com/reel/1176132454682873/` |
| 3 | **Featured CTA card** (orange, 📌 icon) | links to `share/p/1CrVxP9hy2/` — original embed failed because plugins/video.php cannot resolve the video stream from a `/posts/pfbid…` URL, so this slot was repurposed as a high-emphasis CTA pointing to the underlying post |
| 4 | Generic CTA card (blue) | links to fanpage |

### 運動行銷 (`sports-marketing.html`) — 1 video + 3 generic CTAs

| Slot | Content | Source / target |
|---|---|---|
| 1 | Generic CTA card | links to fanpage — reel `952985710920051` was attempted here but FB blocks embedding ("無法使用 — 含有屬於其他人的內容", likely BGM copyright). URL params (`width/height/t=0`) make no difference: this is content-policy, not URL-syntax |
| 2 | Generic CTA card | post `pfbid0Vkm4az…` was attempted here but produced the same `/posts/pfbid…` failure as the original OMO slot 3 |
| 3 | iframe | `facebook.com/reel/1920276022041641/` — only sports embed that works |
| 4 | Generic CTA card | links to fanpage |

> Note: the sports cards render in physical order CTA / CTA / Video / CTA. Visually awkward; consider moving slot 3's video to slot 1 in a follow-up commit so the page leads with content.

**Captions still need copy** — search each file for `[案例名稱]` or `[運動案例` placeholders.

### iframe template (if you need to swap a URL later)

```html
<iframe
  src="https://www.facebook.com/plugins/video.php?href=ENCODED_FB_VIDEO_URL&show_text=false"
  width="500" height="280"
  style="border:none;overflow:hidden" scrolling="no" frameborder="0"
  allowfullscreen="true"
  allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
  loading="lazy"
  title="iFLocus 案例影片"></iframe>
```

### CTA card template (if you want to switch a slot back to "more videos")

```html
<a class="fb-video-card fb-video-cta-card" href="https://www.facebook.com/LOCUS.iFLocus/" target="_blank" rel="noopener noreferrer">
  <div class="fb-video-frame fb-video-cta-frame">
    <span class="fb-video-cta-text">標題 →<br><small>說明</small></span>
  </div>
  <figcaption>caption</figcaption>
</a>
```

### Replacement template (drop in over the `<!-- FB_VIDEO_PLACEHOLDER_... -->` line)

```html
<iframe
  src="https://www.facebook.com/plugins/video.php?href=ENCODED_FB_VIDEO_URL&show_text=false"
  width="500" height="280"
  style="border:none;overflow:hidden" scrolling="no" frameborder="0"
  allowfullscreen="true"
  allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
  loading="lazy"
  title="iFLocus 案例影片"></iframe>
```

The card's CSS `padding-top:56.25%` already forces 16:9, so the iframe's `width`/`height` attrs are nominal — the CSS `position:absolute; inset:0; width:100% !important; height:100% !important` takes over.

## 4. FB embed choice — iframe (confirmed)

Picked `plugins/video.php` iframe over the FB JavaScript SDK. Reasons:
- Static site has no build step or framework; adding a global `<script async>` would hurt LCP across all pages.
- SDK re-parsing across multi-page navigation is fragile, especially with the existing GA snippet already loading.
- When an ad-blocker squashes the FB domain, an iframe collapses to its background colour and our `.fb-video-fallback` (a sibling absolutely-positioned over the frame) stays visible with a「點此前往 FB 觀看」CTA — no blank white box.
- The dark gradient fallback also doubles as a tasteful loading state *before* a URL is even filled in.

## 5. Responsive / fallback test results

Verified via `python -m http.server` preview at native (532 px) and forced 1280 / 375 viewports:

| Test | Result |
|---|---|
| Homepage `.fb-follow-strip` at 1280 px | flex-row, button right-aligned ✅ |
| Same at 375 px | flex-column, button stretches full width ✅ |
| Contact page `.fb-dual-section` at 1280 px | text left, two buttons right ✅ |
| Same at 375 px | stacked, both buttons share equal width via `flex:1` ✅ |
| Video grid at 1280 px (OMO) | 2 columns, 354 px each, no overflow ✅ |
| Video grid at 375 px (OMO) | 1 column, 327 px, no overflow, 16:9 (0.563) ✅ |
| Footer FB link rendered with icon + text site-wide | ✅ (confirmed via shared `js/components.js`) |
| Old「FB Messenger」聯絡資訊 card removed | ✅ |
| No second FB entry added to footer | ✅ |
| Fallback `<div class="fb-video-fallback">` visible while no iframe present | ✅ — `.fb-video-frame > iframe + .fb-video-fallback { display:none }` auto-hides once you drop an iframe in |
| No console errors on any page | ✅ |

> Note: the preview tool's `preview_screenshot` was intermittently timing out (renderer-side, not our code). Verification used `preview_eval` + `preview_snapshot` for measured DOM/computed-style assertions instead — those are stricter than eyeballing a screenshot anyway.

## 6. Flags for Joseph

- **sports-marketing.html is short.** Even with the video grid, the page is content-light (5 sections total). The video block adds bottom weight but ended up as only 1 playable iframe + 3 CTA cards because two intended Reels failed FB-side embed checks (one BGM copyright, one mixed-post-format limitation — see §3). Page would still benefit from body-content expansion (KOL/運動女力 examples, packages, FAQ). **Per your instruction, I did not invent copy** — flagging for Faye's content pass as a separate task.
- **`css/style.css` had pre-existing un-staged tweaks** to `.page-hero.hero-scenic.hero-sports` (background-color/size/position) from before this session. I kept those out of the FB commits so they remain un-staged exactly as you found them. Decide separately whether to commit / discard.
- **GA placeholder.** `contact_us.html` still has `GA_MEASUREMENT_ID` literally hardcoded (lines 26–32). Not in scope for this branch — flagging because it'll matter for 7/1.

---

## 7. Cleanup candidates (NOT deleted — awaiting your call)

### 【可直接刪除】 (safe, no references in any HTML/CSS/JS)

| Path | Size | Why |
|---|---|---|
| `.tmp/panasonic.html` | small | Scratch copy. The Panasonic case is already integrated into `case-studies.html`, `case-event.html`, `case-leisure.html`, `case-3c.html`. The `.tmp/` folder is also untracked in your initial `git status`. |
| `__pycache__/gen_case.cpython-314.pyc` | small | Python bytecode cache. Already gitignored, just rm the on-disk file. |
| `LOGO/LOCUS 簡易版LOGO/png/.DS_Store` | tiny | macOS Finder cruft. |

### 【建議刪除但請確認】

| Path | Size | Why / risk |
|---|---|---|
| `backups/site-before-influence-marketing-20260429-180103/` | 2.3 MB | Snapshot from 2026-04-29 pre-influence-marketing branch. Already gitignored, so deleting it from disk is local-only. Confirm you no longer need this snapshot before nuking. |
| `LOGO/` | 12 MB | Source logo assets (likely `.ai`/`.psd`/etc, judging by size). Already gitignored. **Probably keep on disk** as your master copy — only delete if you have these mirrored elsewhere (Google Drive master, designer handoff folder). Listed for visibility, not because I recommend removal. |
| `internal/` | unknown | Survey/click runners + test fixtures. Already mostly gitignored. If this is your live ops tooling, keep. If it's archived experimentation, can be moved to a separate repo or deleted. |
| `CASE-PAGE-PLAYBOOK.md` | small | Internal dev playbook — useful for future case page additions, but won't be served to public. Either move into a `docs/` folder or add to `.gitignore`. |
| `SUMMARY.md` (this file) | small | This very file. After 7/1 launch, archive or delete — it's task-scoped. |

### 【不確定,請 Joseph 判斷】

| Path | Why uncertain |
|---|---|
| Pre-existing un-staged style.css tweaks (`.hero-sports` lines 745–755 area) | See §6. Not a file to delete — a diff to decide on. |
| 4 untracked `images/external/2016-09 / 2017-07 / 2017-08/*` files in your initial git status | **Corrected after per-file grep audit (was previously listed wrong here as "all 4 in-use").** Actual situation: 2 in-use, 2 orphans. — `2017/07/資策會_智慧城市展_Diamond-Push.jpg` and `2017/07/資策會_智慧城市展_活動頁.jpg` are referenced from `case-leisure.html`. — `2016/09/活動頁.2jpg.jpg` (malformed double-extension save accident) and `2017/08/飛利浦_北六_banner.jpg` (0 grep hits; the HTML references `飛利浦_四六_banner.jpg`, a separate existing file). Resolved in commit `972644e`: 2 in-use added to version control, 2 orphans deleted. |

### 【未掃描 / 超出本任務範圍】

- Full orphan-image audit across `images/**` — would need a more deliberate pass; Chinese-filename URL-encoding in HTML makes a naive grep noisy. Flag if you want me to run that as a separate task.

### Recommended .gitignore additions (when you confirm cleanup)

```
.DS_Store
Thumbs.db
*.bak
*.tmp
*.swp
.tmp/
```

(Your current `.gitignore` already covers `__pycache__/`, `*.pyc`, `backups/`, `LOGO/`, `.claude/`, and most of `internal/`.)

---

**Next step**: tell me which rows under §7【可直接刪除】and【建議刪除但請確認】to remove. I'll then `git rm` them, update `.gitignore`, run a final preview check across all pages, and make the `chore:` commit.

---

## 8. 未清理項目 — 7/1 後評估

Cleanup pass executed across commits `972644e`, `f9cc41b`, `b323d46`. The following were **intentionally left in place** for now and should be re-evaluated after 7/1 launch stabilises:

### Assets retained pending future use
- `images/page-assets/` — 7 unused but purposefully-named files (`brand-team-joseph.jpg`, `brand-team-faye.jpg`, `brand-service-overview.jpg`, `video-case-links-1.jpg`, `video-case-links-2.jpg`, `video-hero-clean.jpg`, `sports-impact-plan.jpg`). Look like pre-staged assets for sections not yet wired up.
- `images/external/` orphans deferred — 20 files: `great-case-02/03/06/07.png`, `nissen.png`, the `2022/12/*` long-tail (10 files), and `2023/07/iFLocus-網頁-v3-*` (5 files). All 0 references, but kept because they may be needed as a content-pass restores history pages.

### Already gitignored — disk cleanup deferred
- `change-log.md`, `hidden-pages-ppt-classification.md` — ignored from version control, still on disk.
- `internal/` — survey / clicks runners + test fixtures. Treated as live ops tooling pending confirmation.
- `backups/site-before-influence-marketing-20260429-180103/` — 2.3 MB snapshot. Reclaim after 7/1.
- `LOGO/` — 12 MB design source masters. Keep on disk; gitignored already.

### Numbering oddity (not a cleanup item)
- `images/iflocus-XX.jpg` series goes 56–62, then jumps to 64. `iflocus-63.jpg` does not exist on disk and is not referenced anywhere — confirmed below (D-3 check). Likely an intentional skip, not a missing upload.
