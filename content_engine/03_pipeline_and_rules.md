# LAZYMETA PIPELINE & SYSTEM RULES (v3.0)
## Campaign Folders, JSON/TXT Captions & Automated Scheduling Rules

---

## 1. CAMPAIGN FOLDER STRUCTURE (RECOMMENDED)

Organizing by campaign folder keeps each niche cleanly isolated and portable:

```text
lazymeta/
├── campaigns/                   # Store all your 30-day niche campaigns here
│   ├── webdev_mastery/          # Niche A
│   │   ├── captions.json        # Structured post data & photo mappings
│   │   └── images/              # 01.jpg, 02.jpg ... 90.jpg
│   └── ecommerce_growth/        # Niche B
│       ├── captions.json
│       └── images/
├── content_engine/              # Content generation prompts & guides
├── .env                         # Meta API credentials (strictly gitignored)
└── run.py                       # CLI entry point
```

To schedule or preview a campaign, simply run:
```bash
python run.py preview --campaign campaigns/webdev_mastery
python run.py schedule --campaign campaigns/webdev_mastery
```

*(Note: Traditional root `captions.txt` / `captions.json` and `images/` folder also remain 100% supported if you prefer root execution.)*

---

## 2. `captions.json` FORMAT (CLEANEST & MACHINE-READABLE)

Using `captions.json` eliminates delimiter errors, allows multi-photo carousels, and lets you store prompt metadata right alongside each post:

```json
[
  {
    "id": 1,
    "day": 1,
    "slot": "morning",
    "images": ["01.jpg"],
    "caption": "অধিকাংশ ফ্রিল্যান্সার ভাবে তাদের কাজ না পাওয়ার কারণ 'কমিউনিকেশন স্কিল'। ⚡\nকিন্তু বাস্তব সত্যিটা শুনলে আপনার চোখ কপালে উঠবে...\n\n#FreelanceStrategy #ClientAcquisition"
  },
  {
    "id": 2,
    "day": 1,
    "slot": "afternoon",
    "images": ["02a.jpg", "02b.jpg"],
    "caption": "This 2-slide carousel breaks down leverage vs brute force! 🚀\n\nSwipe to inspect the architecture."
  }
]
```

* **Single Photo Post:** `"images": ["01.jpg"]` or `"images": "01.jpg"`.
* **Multi-Photo Carousel:** `"images": ["02a.jpg", "02b.jpg"]`.
* **Implicit Pairing:** If you leave `"images"` empty or omit it, LazyMeta automatically pairs posts with available files in `images/` sequentially!

---

## 3. `captions.txt` SYNTAX & FORMATTING RULES (ALTERNATIVE)


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
