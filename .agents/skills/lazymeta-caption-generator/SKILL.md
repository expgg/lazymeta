---
name: lazymeta-caption-generator
description: Generate production-ready 30-day (90-post) social media captions formatted strictly for LazyMeta bulk scheduling with optimal hooks, line breaks, emojis, hashtags, and image mappings.
---

# LazyMeta Caption Generator Skill

Use this skill whenever you are tasked with generating social media captions for bulk scheduling with **LazyMeta**. 

LazyMeta automates 30 days of posting (3 posts/day = 90 posts) directly to Meta's servers. To ensure seamless ingestion, every caption generated **MUST** adhere strictly to the format, spacing, and metadata rules below.

---

## 1. Syntax & Delimiter Rules

### The `---` Divider (Mandatory)
* Every single post **must** be separated by a markdown divider `---` on its own line.
* Do not put spaces before or after `---`.
* Do not use `***` or `===`.

### Image Association Header (Optional but Powerful)
* **Auto-Pairing Mode (Recommended):** If images in the `images/` folder are named sequentially (`01.jpg` to `90.jpg`), **omit** the image header. LazyMeta pairs them automatically in natural numerical order.
* **Explicit Single Image:**
  ```text
  images: summer_launch.jpg
  ```
* **Multi-Image Carousel:** Separate filenames with commas:
  ```text
  images: slide_01.png, slide_02.png, slide_03.png
  ```

---

## 2. Anatomy of a High-Converting Post

Every generated post must follow this exact 5-part structure:

```text
---
[Optional images: header]
[1. The Hook Line] 🚀

[2. The Core Value / Story / Body]
[Keep paragraphs 1 to 2 sentences max. Use blank lines between paragraphs.]

[3. The Call to Action (CTA)] 👇

[4. 3 to 5 Targeted Hashtags]
```

### Example:
```text
---
images: productivity_guide.jpg
The biggest mistake founders make with automation is waiting too long. 💡

You don't need a 50-person team to automate your repetitive distribution.

Batch your content once a month. Schedule the entire 30-day queue in 4 minutes, and let Meta's servers do the distribution while you focus on building.

What is one task you wish you could automate today? Drop it below! 👇

#FounderTips #AutomationTools #ProductivityHacks #StartupGrowth
---
```

---

## 3. Formatting & Copywriting Guidelines

### A. Line Breaks & Spacing
* **Never** write walls of text. Social media audiences skim.
* Use a **single blank line** between every paragraph.
* **Never** use HTML tags like `<br>` or `<p>`. Standard clean text newlines are preserved by LazyMeta and rendered natively by Meta Graph API.

### B. Emoji Rules
* **Quantity:** 2 to 4 emojis per post maximum.
* **Placement:** Place emojis at the end of the hook line, next to bullet points (⚡, 📌, ✅), or pointing to actions (👇, 🔗).
* **Restraint:** Never cluster consecutive emojis (avoid `🔥🔥🔥🚀🚀🚀`). It triggers spam filters and looks amateur.

### C. Hashtag Standards
* **Quantity:** Exactly 3 to 5 hashtags per post.
* **Format:** Place all hashtags on the very last line of the post.
* **Casing:** Use CamelCase for readability (e.g., `#SocialMediaStrategy`, not `#socialmediastrategy`).
* **Relevance:** Include 1 broad tag (`#Marketing`), 2 niche tags (`#MetaGraphAPI`, `#ContentOperations`), and 1 community tag (`#BuildInPublic`).

---

## 4. The 30-Day Queue Rhythm (3 Posts Per Day)

When generating a full 90-post queue for 30 days, follow this natural engagement cadence:

| Time Slot | Post Theme | Objective & Angle |
| :--- | :--- | :--- |
| **09:00 AM** (Morning) | **Inspiration & Industry News** | Quick tips, motivation, industry observations, thought-provoking statements. |
| **02:00 PM** (Afternoon) | **Educational Deep-Dive / Carousel** | Step-by-step how-to, visual carousel breakdown, case study, workflow teardown. |
| **08:00 PM** (Evening) | **Community Engagement & Polls** | Relatable questions, conversation starters, humor, "This or That" choices. |

---

## 5. Output Directives for AI Agents

When the user asks you to generate a `captions.txt` file:
1. **Do not** output conversational preambles like "Sure! Here are your 90 captions:".
2. **Do not** wrap the output in unnecessary markdown explanation blocks unless asked.
3. Start directly with the first `---` divider.
4. Verify that the total number of posts matches the user's requested count (e.g. exactly 90 posts for a 30-day queue).
5. Ensure every post has distinct, engaging copy with zero duplicate text.
