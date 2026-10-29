# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-29

### Initial Release

#### 🚀 Features
- **High-Throughput 30-Day Scheduling:** Automatically queues up to 90 posts across 30 days (3 posts/day) directly to Meta's servers in ~3 minutes.
- **Client-Side Guardrails:** Hard enforcement of Meta's strict 10-minute to 30-day scheduling window. Automatic slot rollover and 15-minute safety buffer against network clock drift.
- **Spam Defense & Rate-Limiting:** Mandatory 2.5-second jittered request delay ($2.0\text{s} - 3.0\text{s}$) paired with automatic exponential backoff for HTTP 429 and Meta Error Codes 4 and 17.
- **Dual Dispatch Architecture:**
  - Single-photo direct publishing via `POST /{page-id}/photos`.
  - Multi-photo / carousel publishing via two-step unpublished photo staging and scheduled `POST /{page-id}/feed` story.
- **Pre-Flight Health Doctor (`lazymeta doctor`):** Automated checks verifying Page ID, token status, permissions (`pages_manage_posts`, `pages_read_engagement`), and git repository credential safety.
- **Dry-Run Preview (`lazymeta preview`):** Formats complete 30-day timeline table with post indexes, image files, types, and caption snippets before making any API requests.
- **Atomic State Journaling:** State manager (`.lazymeta_state.json`) logs every scheduled post ID to allow seamless resume after interruptions without duplicating posts.
- **Meta Server Status Inspector (`lazymeta status`):** Queries and visualizes posts currently queued on Meta's servers for your page.
- **Natural Image Sorting:** Automatically sorts images with natural numerical ordering (`img_1.jpg`, `img_2.jpg`, `img_10.jpg`).

#### 🔒 Security
- Strict `.gitignore` protecting `.env`, state journals, logs, and media folders.
- Git credential audit that alerts users if secrets are ever accidentally tracked in version control.
