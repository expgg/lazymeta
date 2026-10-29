---
name: lazymeta-caption-generator
description: Generate production-ready 30-day (90-post) social media captions formatted strictly for LazyMeta bulk scheduling with optimal hooks, line breaks, emojis, hashtags, folder structure, and image mappings.
---

# LazyMeta Caption & Media Queue Generator Skill

Use this skill whenever you are tasked with preparing, formatting, or generating social media content for bulk scheduling with **LazyMeta**. 

LazyMeta automates 30 days of posting (3 posts/day = 90 posts) directly to Meta's servers. To ensure seamless ingestion, every file, image name, and caption generated **MUST** adhere strictly to the folder layout, photo naming patterns, and delimiter syntax below.

---

## 📁 1. Project Directory & Folder Structure

All campaign files must be organized in this exact structure:

```text
lazymeta/
├── captions.txt                  # The single file containing all 90 caption blocks
└── images/                       # Folder containing all 90+ image files
    ├── 01.jpg                    # Day 1, Post 1 (09:00 AM)
    ├── 02.jpg                    # Day 1, Post 2 (02:00 PM)
    ├── 03.jpg                    # Day 1, Post 3 (08:00 PM)
    ├── 04.jpg                    # Day 2, Post 1 (09:00 AM)
    ├── ...
    └── 90.jpg                    # Day 30, Post 3 (08:00 PM)
```

*(Note: Custom paths can be passed to LazyMeta via `--images path/to/images --captions path/to/captions.txt`)*.

---

## 🏷️ 2. Photo & Image Naming Conventions

LazyMeta automatically sorts and matches images. Use one of the three standard naming patterns:

### Pattern A: Two-Digit Padded Sequential (Recommended for 90-Post Queues)
Best for 1-to-1 auto-pairing without typing image names into `captions.txt`:
* **Naming Scheme:** `01.jpg`, `02.jpg`, `03.jpg`, ... `10.jpg`, ... `90.jpg`  
  *(or `post_01.jpg` to `post_90.jpg`)*
* **Padding Rule:** Always use two-digit padding (`01` through `09`) so operating systems and natural sorting engines order files chronologically (`01`, `02`, ... `10`, not `1`, `10`, `2`).
* **In `captions.txt`:** You **omit** the `images:` line completely. Post #1 automatically pairs with `01.jpg`, Post #2 with `02.jpg`, etc.

### Pattern B: Day & Slot Identifier (Best for Calendar Clarity)
Ideal if you prefer explicit timestamps in file names:
* **Morning (09:00 AM):** `day01_morning.jpg` (or `day01_1.jpg`)
* **Afternoon (02:00 PM):** `day01_afternoon.jpg` (or `day01_2.jpg`)
* **Evening (08:00 PM):** `day01_evening.jpg` (or `day01_3.jpg`)
* **In `captions.txt`:** Add `images: day01_morning.jpg` as the first line of the block.

### Pattern C: Multi-Photo Carousel Naming
When a single post contains multiple slides or photos (e.g. Post #2 is a 3-slide carousel):
* **Naming Scheme:** `{post_number}_{slide_number}.{ext}`
  * `02_slide1.jpg`
  * `02_slide2.jpg`
  * `02_slide3.jpg`
* **In `captions.txt`:** Reference all slide filenames separated by commas:
  ```text
  ---
  images: 02_slide1.jpg, 02_slide2.jpg, 02_slide3.jpg
  Your carousel caption goes here...
  ```

### Image Specifications:
* **Supported Formats:** `.jpg`, `.jpeg`, `.png`, `.webp`
* **Recommended Aspect Ratios:** `1080x1080` (Square 1:1) or `1080x1350` (Portrait 4:5)
* **Maximum File Size:** Under 10MB per image (under 5MB recommended for fast upload)

---

## 📝 3. Syntax & Delimiter Rules

### The `---` Divider (Mandatory)
* Every single post **must** be separated by a markdown divider `---` on its own line.
* Do not put spaces before or after `---`.
* Do not use `***` or `===`.

### Header vs Auto-Pairing
* **With Header (Explicit or Carousel):**
  ```text
  ---
  images: 01.jpg
  Caption text...
  ---
  images: 02_slide1.jpg, 02_slide2.jpg
  Carousel caption text...
  ```
* **Without Header (Auto-Pairing Mode):**
  ```text
  ---
  Post #1 caption (automatically gets 01.jpg)...
  ---
  Post #2 caption (automatically gets 02.jpg)...
  ```

---

## ✍️ 4. Post Formatting & Style Directives

While AI writes the creative copy, it **must** respect these layout rules:

1. **Line Breaks:** Use a **single blank line** between paragraphs. Never output huge walls of unbroken text. Do not use `<br>` or HTML tags.
2. **Hook Line:** First line must be a punchy hook + 1 relevant emoji.
3. **Emojis:** Use 2 to 4 emojis max per post. Functional only (e.g. bullets ⚡, pointers 👇). Never cluster `🔥🔥🔥`.
4. **Hashtags:** Exactly 3 to 5 CamelCase hashtags (e.g. `#GrowthHacking #SocialStrategy`) placed at the very bottom line.
5. **Cadence (3 Posts / Day):**
   * **09:00 AM (Morning):** Educational insight, inspiration, industry tip.
   * **02:00 PM (Afternoon):** Deep-dive case study, process walkthrough, carousel.
   * **08:00 PM (Evening):** Community question, poll, reflection, conversation starter.

---

## 🤖 5. Directives for AI Output

When generating `captions.txt`:
1. Output **strictly the raw caption text**. Do not include conversational greetings ("Here are your posts!").
2. Start directly with the first `---` divider.
3. If asked for 30 days, ensure exactly **90 posts** are generated (3 posts per day $\times$ 30 days).
