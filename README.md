<div align="center">

# ⚡ LazyMeta

### *High-Throughput 30-Day Automated Bulk Scheduler for Meta Graph API*

[![CI](https://github.com/expgg/lazymeta/actions/workflows/ci.yml/badge.svg)](https://github.com/expgg/lazymeta/actions)
[![Release](https://img.shields.io/github/v/release/expgg/lazymeta?color=blue&logo=github)](https://github.com/expgg/lazymeta/releases)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?logo=python)](https://www.python.org/)
[![Meta Graph API](https://img.shields.io/badge/Meta%20Graph%20API-v22.0-1877F2?logo=meta)](https://developers.facebook.com/docs/graph-api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<p align="center">
  <b>Eliminate manual social media scheduling entirely.</b><br>
  Take a folder of 90 images and a single text file of captions and hashtags, run one command, and have Meta accept the entire 30-day queue (3 posts per day) in under 4 minutes.<br>
  Once uploaded, your computer can be turned off, and Meta's cloud servers publish your content automatically on schedule.
</p>

</div>

---

## 📑 Table of Contents

- [The Philosophy](#-the-philosophy)
- [Architecture Overview](#-architecture-overview)
- [How Gotchas & Complications Are Solved](#-how-gotchas--complications-are-solved)
- [Quick Start](#-quick-start)
- [Obtaining Your Facebook Credentials](#-obtaining-your-facebook-credentials)
- [Captions File Formatting](#-captions-file-formatting)
- [CLI Command Reference](#-cli-command-reference)
- [Meta API Error Code Troubleshooting](#-meta-api-error-code-troubleshooting)
- [Testing](#-testing)
- [Contributing & License](#-contributing--license)

---

## 🎯 The Philosophy

Content creators and businesses spend dozens of hours every month manually dragging images into Meta Business Suite, copy-pasting captions, and clicking date pickers for 90 separate posting slots.

**LazyMeta solves this with a single command:**
1. Point it to a folder of 90 images.
2. Provide a single text file (`captions.txt`) with your captions and hashtags separated by `---`.
3. LazyMeta validates the entire batch, calculates safe timestamps, and dispatches them directly to Meta's servers with anti-spam pacing.
4. **Turn off your computer.** Meta publishes every single post on time from its own infrastructure.

---

## 🏗️ Architecture Overview

```text
┌────────────────────────┐      ┌────────────────────────┐
│     images/ folder     │      │      captions.txt      │
│   (90 sorted images)   │      │   (markdown dividers)  │
└───────────┬────────────┘      └───────────┬────────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
              ┌───────────────────────────┐
              │     Parser & Matcher      │
              │  - Auto-pairing           │
              │  - Carousel detection     │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │     Schedule Engine       │
              │  - 3 daily slots (9/2/8)  │
              │  - 10m - 30d guardrails   │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │   Pre-Flight Validator    │
              │  - Token health & scopes  │
              │  - Git security audit     │
              └─────────────┬─────────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
   ┌───────────────────────┐ ┌───────────────────────┐
   │  Single Image Post    │ │  Multi-Image Post     │
   │  POST /{page}/photos  │ │  1. POST photos (unpub)│
   │  published=false      │ │  2. POST feed (story) │
   └───────────┬───────────┘ └───────────┬───────────┘
               │                         │
               └────────────┬────────────┘
                            ▼
              ┌───────────────────────────┐
              │  Rate Limiter & Backoff   │
              │  - 2.5s jittered delay    │
              │  - Exponential backoff    │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │    Meta Graph API v22     │
              │    (Scheduled in Cloud)   │
              └───────────────────────────┘
```

---

## 🛡️ How Gotchas & Complications Are Solved

| Meta API Gotcha | The Risk | How LazyMeta Solves It |
| :--- | :--- | :--- |
| **Rigid 30-Day Window** | Meta strictly rejects posts scheduled $< 10\text{ min}$ or $> 30\text{ days}$ in advance. | Enforces a client-side **15-minute safety buffer** (automatically skipping past slots) and caps the ceiling at **29 days, 23 hours**. All 90 timestamps are validated upfront before sending any API requests. |
| **Spam Defenses & Rate Limits** | Rapidly firing 90 uploads triggers `HTTP 429` / Error code `4` account blocks. | Paces requests with a mandatory **2.5s jittered delay** ($2.0\text{s} - 3.0\text{s}$) paired with automatic **exponential backoff retry adapter** on transient errors. |
| **Token Invalidation** | Security events on your personal Facebook account revoke Page Access Tokens silently. | `lazymeta doctor` and pre-flight startup checks ping Meta to verify token validity, Page ID ownership, and `pages_manage_posts` permissions. |
| **Single vs. Multi-Image** | Carousels cannot be scheduled in a single request like single photos. | **Dual-pipeline dispatcher:** Single photos hit `POST /{page-id}/photos`. Multi-image carousels upload unattached photos unpublished first, then schedule a `POST /{page-id}/feed` story referencing `attached_media`. |
| **API Version Deprecations** | Meta updates Graph API versions quarterly and deprecates older endpoints. | Graph API version is parameterized in `.env` (`META_GRAPH_VERSION=v22.0`). Upgrades require editing a single configuration line. |
| **Secret Leakage Risks** | Committing access tokens to GitHub risks permanent page takeover. | Pre-configured `.gitignore` blocks `.env`, state files, and media. Pre-flight check audits git index and warns if `.env` is ever tracked. |
| **Interrupted Runs** | Network failure on post #45 would cause duplicate posts if re-run. | **Atomic State Journal (`.lazymeta_state.json`):** Tracks each scheduled post ID. Re-running automatically resumes where it stopped. |

---

## 🚀 Quick Start

### 1. Prerequisites & Installation

Ensure you have Python 3.10 or higher installed:

```bash
git clone https://github.com/expgg/lazymeta.git
cd lazymeta
pip install -r requirements.txt
```

*(Optional)* Install locally as a command-line tool:
```bash
pip install -e .
```

### 2. Configure Credentials

Copy the template environment file:
```bash
cp .env.example .env
```
Edit `.env` with your favorite text editor:
```env
META_PAGE_ID=your_page_id_here
META_PAGE_ACCESS_TOKEN=your_permanent_page_access_token_here
META_GRAPH_VERSION=v22.0
META_REQUEST_DELAY=2.5
```

### 3. Verify Health & Permissions

Run the pre-flight doctor:
```bash
python run.py doctor
```
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ LazyMeta v1.0.0                                                             │
│ High-Throughput 30-Day Automated Bulk Scheduler for Meta Graph API          │
└─────────────────────────────────────────────────────────────────────────────┘
Running Pre-Flight Health Checks...

✓ Git Security: Credentials are not tracked in git.
✓ Configuration: API Version: v22.0, Delay: 2.5s
✓ Meta Connection: Successfully connected as Brand Official (ID: 100998877)
✓ Publishing Permissions: Page posting rights verified.

All systems operational! LazyMeta is ready to schedule.
```

### 4. Preview The 30-Day Schedule (Dry Run)

Simulate your queue without making any network calls to Meta:
```bash
python run.py preview --images sample_data/images --captions sample_data/captions.txt
```

### 5. Launch the Live Queue

Execute the live scheduling loop:
```bash
python run.py schedule --images ./images --captions ./captions.txt
```

---

## 🔑 Obtaining Your Facebook Credentials

### Step 1: Find Your Numeric Page ID
1. Open your Facebook Page in a browser.
2. Click **Settings** $\rightarrow$ **Page Setup** (or look at the URL / **About** tab).
3. Copy your numeric **Page ID** (e.g., `102938475610293`).

### Step 2: Generate a Permanent Page Access Token
> **Warning:** Never use a standard User Token. User tokens expire and cannot schedule unpublished page photos.

1. Go to the [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. In the top-right corner, select your **Facebook App**.
3. Under the **User or Page** dropdown, select your **Facebook Page**.
4. In the **Permissions** panel, ensure both permissions are added:
   - `pages_manage_posts`
   - `pages_read_engagement`
5. Click **Generate Access Token** and approve the permissions.
6. **For a permanent production token:**
   - Go to [Meta Business Suite](https://business.facebook.com/) $\rightarrow$ **Settings** $\rightarrow$ **System Users**.
   - Create a System User with the **Employee** or **Admin** role.
   - Assign your Facebook Page to the system user with full content publishing permissions.
   - Click **Generate New Token**, select `pages_manage_posts` and `pages_read_engagement`, and choose **Never Expire**.
   - Copy this token into your `.env` file as `META_PAGE_ACCESS_TOKEN`.

---

## 📝 Captions File Formatting

LazyMeta uses standard markdown dividers (`---`) to separate posts in `captions.txt`.

### Mode A: Automatic Sequential Pairing (Recommended for 90 Images)
If you have 90 images (`img_01.jpg` to `img_90.jpg`), simply write 90 caption blocks. LazyMeta automatically pairs each post with the sorted image from `--images`:

```text
---
🚀 Product launch announcement! We are thrilled to show you our new design.
Link in bio to read the full case study.
#design #product #launch
---
📸 Behind the scenes of our team offsite this quarter.
What goals are you tackling this month?
#teamwork #culture #startuplife
---
💡 Quick tip: Automate your repetitive workflows to unlock creative focus.
#productivity #automation #growth
```

### Mode B: Explicit Image Association & Multi-Photo Carousels
To associate specific filenames or create **multi-photo carousel posts**, include an `images:` header:

```text
---
images: hero_shot.jpg
Single image post caption here!
#marketing #socialmedia
---
images: slide1.png, slide2.png, slide3.png
Swipe through our 3-part guide to content strategy! 👉
Which slide was most helpful?
#carousel #contentstrategy #education
---
```

---

## 💻 CLI Command Reference

### `doctor`
Validates configuration, git tracking safety, Meta token status, and publishing scopes:
```bash
python run.py doctor [--env-file .env]
```

### `preview`
Calculates timestamps across 30 days and displays a Rich terminal table:
```bash
python run.py preview \
  --images ./images \
  --captions ./captions.txt \
  --slots "09:00,14:00,20:00" \
  --start-date 2026-11-01
```

### `schedule`
Executes the batch queue with live progress bar and rate-limiting:
```bash
python run.py schedule \
  --images ./images \
  --captions ./captions.txt \
  --slots "09:00,14:00,20:00" \
  --yes
```
**Flags:**
* `-i, --images <DIR>`: Directory containing image files (default: `images`).
* `-c, --captions <FILE>`: Captions file with `---` dividers (default: `captions.txt`).
* `-s, --slots <HH:MM,HH:MM,...>`: Daily posting times (default: `09:00,14:00,20:00`).
* `-d, --start-date <YYYY-MM-DD>`: Starting date (default: today or earliest valid slot).
* `-y, --yes`: Non-interactive mode (skips confirmation prompt).
* `--dry-run`: Runs all calculations and pre-flight checks without calling Meta.
* `--reset-state`: Clears previous session state journal before starting.

### `status`
Inspects scheduled posts currently waiting in Meta's server queue:
```bash
python run.py status --limit 30
```

### `reset-state`
Clears the local `.lazymeta_state.json` file:
```bash
python run.py reset-state
```

---

## 🔍 Meta API Error Code Troubleshooting

| Error Code | Meaning | Root Cause & Resolution |
| :--- | :--- | :--- |
| **`190` / `460`** | `OAuthException: Invalid Access Token` | The Page Access Token was invalidated because your personal account changed password, reset 2FA, or logged out of all devices. Generate a fresh Page Access Token. |
| **`4` / `17`** | `User request limit reached` | Meta spam defense triggered due to too many requests. LazyMeta automatically sleeps and retries with backoff. If repeated, increase `META_REQUEST_DELAY=3.5` in `.env`. |
| **`100`** | `Param scheduled_publish_time is invalid` | The requested timestamp falls outside Meta's allowable window ($< 10\text{ min}$ or $> 30\text{ days}$). LazyMeta prevents this client-side, but ensure your computer clock is synchronized. |
| **`200`** | `Permission Denied` | The token lacks `pages_manage_posts` or you do not have Admin/Editor role on the target Page. |

---

## 🧪 Testing

LazyMeta includes a comprehensive test suite covering parser edge cases, natural sorting, 10m-30d boundary enforcement, carousel payload structures, and state journaling:

```bash
pytest -v
```

```text
============================= test session starts =============================
tests/test_api.py::test_verify_credentials_success PASSED                [  9%]
tests/test_api.py::test_verify_credentials_revoked_token PASSED          [ 18%]
tests/test_api.py::test_schedule_single_photo_call PASSED                [ 27%]
tests/test_parser.py::test_natural_sort_key PASSED                       [ 36%]
tests/test_parser.py::test_parse_captions_with_image_headers PASSED      [ 45%]
tests/test_parser.py::test_parse_captions_auto_pairing PASSED            [ 54%]
tests/test_parser.py::test_validate_posts_missing_image PASSED           [ 63%]
tests/test_scheduler.py::test_schedule_plan_90_posts PASSED              [ 72%]
tests/test_scheduler.py::test_schedule_rejects_past_30_days PASSED       [ 81%]
tests/test_scheduler.py::test_schedule_skips_slots_within_15_minutes PASSED [ 90%]
tests/test_state.py::test_state_manager_lifecycle PASSED                 [100%]

============================= 11 passed in 1.12s ==============================
```

---

## 📄 Contributing & License

Contributions are welcome! Please review [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md) before opening a pull request.

Released under the [MIT License](LICENSE).
