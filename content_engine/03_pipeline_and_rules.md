# LAZYMETA PIPELINE & SYSTEM RULES (v3.0)
## Folder Structure, File Conventions & Automated Scheduling Rules

---

## 1. FILE & DIRECTORY STRUCTURE

To run a 30-day automated queue without errors, set up your project directory like this:

```text
lazymeta/
├── content_engine/
│   ├── 01_text_engine.md        # Copywriting, pre-fold hooks & 5 viral buckets
│   ├── 02_image_engine.md       # High-hook 2.5D editorial vector prompt engine
│   └── 03_pipeline_and_rules.md # This pipeline, folder structure & CLI guide
├── images/                      # Generated visual assets
│   ├── 01.jpg
│   ├── 02.jpg
│   ├── ...
│   └── 90.jpg
├── captions.txt                 # All 90 posts separated by '---'
├── .env                         # Meta API credentials (strictly gitignored)
├── run.py                       # CLI entry point
└── .lazymeta_state.json         # Auto-generated sync state
```

---

## 2. IMAGE CONVENTIONS & MAPPING

* **Naming Format:** Save images sequentially as `01.jpg`, `02.jpg`, ..., `90.jpg` (supported extensions: `.jpg`, `.jpeg`, `.png`, `.webp`).
* **Direct Feed Publishing:** Drop images straight from your AI image generator into `images/`. No Adobe Illustrator conversion needed.
* **Aspect Ratio:** `1:1` (1080x1080) or `4:5` (1080x1350) for maximum mobile feed real estate.
* **Single Photo Post:** Implicit matching (Post 1 gets `images/01.jpg`, Post 2 gets `images/02.jpg`) OR explicit header: `images: 01.jpg`.
* **Multi-Photo Carousel:** Comma-separated list in the post header:
  ```text
  ---
  images: 05a.jpg, 05b.jpg, 05c.jpg
  Post text here...
  ---
  ```

---

## 3. `captions.txt` SYNTAX & FORMATTING RULES

1. **The Post Delimiter (`---`):**
   * Every single post MUST start and end with `---` on its own line.
   * Never insert `---` inside the post body.
2. **Explicit Image Header (Optional):**
   * If you want to explicitly map an image, put `images: [filename]` on the line directly following the opening `---`.
   * If omitted, LazyMeta automatically maps Post #1 $\rightarrow$ `images/01.jpg`, Post #2 $\rightarrow$ `images/02.jpg`, etc.
3. **Paragraph Spacing & Newlines:**
   * Leave a single blank line between paragraphs.
   * Standard clean newlines are preserved natively by Meta Graph API.
   * Never use HTML tags like `<br>`.

### Clean `captions.txt` Example:
```text
---
images: 01.jpg
Line 1: Hook that breaks the scroll ⚡
Line 2: Retention bridge that deepens intrigue
Line 3: Open loop cliffhanger that forces "...See more"

Body paragraph with actionable insight.

The punchline / epiphany takeaway. 💡

Penalty-free comment question? 👇

#Tag1 #Tag2 #Tag3 #Tag4
---
images: 02.jpg
Line 1: Second post hook 🚀
Line 2: Retention bridge
Line 3: Open loop cliffhanger

Second post body paragraph.

The punchline takeaway. 💡

Comment question? 👇

#Tag1 #Tag2 #Tag3 #Tag4
---
```

---

## 4. SCHEDULING CADENCE & INTERVALS

* **Default Cadence:** **3 posts per day for 30 days = 90 posts total**.
* **Daily Time Slots:** Posts are automatically spaced across optimal mobile engagement hours (e.g. Morning `09:00`, Afternoon `14:00`, Evening `20:00`, or evenly distributed across 480-minute intervals).
* **Meta Graph API Constraints:** 
  * Posts must be scheduled at least **10 minutes** in the future.
  * Posts cannot be scheduled more than **75 days** in the future.
  * LazyMeta's scheduling engine validates and enforces these bounds automatically.

---

## 5. CLI COMMANDS & WORKFLOW

### Step 1: Pre-Flight Doctor Check
Validate your Meta credentials, Page Access Token, and publishing permissions:
```bash
python run.py doctor
```

### Step 2: Dry-Run Preview
Inspect all parsed captions, image pairings, character counts, and calculated timestamps without uploading anything:
```bash
python run.py preview
```

### Step 3: Launch Bulk Scheduler
Upload media and publish all 90 scheduled posts directly into Meta's servers:
```bash
python run.py schedule
```
*(Once complete, you can shut down your computer. Meta's servers will publish each post on schedule.)*

### Step 4: Check Scheduled Status
View current progress, scheduled counts, and remaining queue:
```bash
python run.py status
```

### Step 5: Reset State (If Needed)
To re-run or test a fresh schedule:
```bash
python run.py reset-state
```
