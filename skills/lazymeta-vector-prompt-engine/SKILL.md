---
name: lazymeta-vector-prompt-engine
description: Generate ultra-precise, silkscreen trace-optimized image prompts for Google AI Flow, Imagen 3, or ImageFX, mapped directly to LazyMeta 30-day queues (01.jpg - 90.jpg).
---

# LazyMeta Vector Art & Trace-Optimized Prompt Engine

Use this skill when you need to generate high-contrast, flat silkscreen vector illustrations for social media posts that can be **cleanly traced into `.ai` vector paths via Adobe Illustrator** and scheduled seamlessly with **LazyMeta**.

---

## 1. Core Production Pipeline

```text
Post Topic / captions.txt
        │
        ▼
[This Prompt Engine]
        │
        ▼
Google AI Flow / Imagen 3 / ImageFX (Pure White Background, Flat Colors)
        │
        ▼
Adobe Illustrator Auto-Trace (scripts/Auto_Image_Trace_Expand.jsx -> Ignore White)
        │
        ▼
images/01.jpg ... 90.jpg
        │
        ▼
LazyMeta Bulk Scheduler (python run.py schedule)
```

---

## 2. Technical Art Constraints (Vector Optimization)

Every prompt MUST enforce:
* **Art Style:** Silkscreen print aesthetic, flat vinyl sticker look, clean corporate 2D tech editorial flat vector art (Linear / Notion / Stripe illustration aesthetic).
* **Composition:** Maximum 1 or 2 focal elements (faceless human interacting with one oversized metaphorical prop).
* **Faceless Characters:** Clean silhouettes, warm peach or golden skin tone, thick limbs, zero facial features, clearly segmented clothing colors.
* **Background:** 100% pure flat white (`#ffffff`) with generous negative space.
* **Color Palette:** Exactly 4 to 5 flat solid colors (Zero gradients, zero shadows, zero reflections).
* **Aspect Ratios:** `1:1` (Square 1080x1080) for feed, or `4:5` (Portrait 1080x1350) for maximum mobile feed space.
* **Minimal Tech Typography & Badges (Encouraged):** Clean geometric badges, code tags, or status pills (e.g. `API`, `v2.0`, `SQL`, `404`) that add high-end editorial tech credibility.
* **Banned:** No paragraph text, no AI gibberish text, no plastic sluggish AI blurs, no gradient transitions, no floating confetti, no drop shadows.

---

## 3. Communication Protocol
* Explain the visual concept and Illustrator advice in **Bengali (বাংলা)**.
* Write the actual **Main Prompt** and **Negative Prompt** in **English** for maximum Imagen accuracy.
* Include the mapping file name (e.g. `01.jpg`, `02.jpg`, etc.) so it matches LazyMeta's queue.

---

## 4. Prompt Template

```markdown
### 🖼️ Post [XX] -> `[XX].jpg`

**১. সংক্ষিপ্ত কনসেপ্ট (Bengali):**
[১-২ লাইনের ব্যাখ্যা]

**২. Main Image Prompt (English):**
> Silkscreen print aesthetic, ultra-clean minimal 2D vector graphic of [SUBJECT & ACTION], 1:1 square aspect ratio composition. Central composition features a single stylized faceless person shown in side profile with smooth warm peach skin tone, wearing a solid light white crewneck t-shirt, dark navy blue trousers, and minimal dark shoes. The person is purposefully interacting with [OVERSIZED PROP], composed of [PRECISE 2-3 FLAT COLOR BLOCKS]. Pure 2D flat silhouette shapes, thick purposeful contours, strictly uniform flat color fills with zero internal gradation. Surrounded by generous empty negative space. Isolated on an immaculate, solid pure white background (#ffffff). High edge contrast, knife-sharp vector boundaries with 100% opacity, optimized for Adobe Illustrator Image Trace and SVG vector path expansion. No floating icons, no text, no code snippets, no letters, no typography, aspect ratio 1:1.

**৩. Negative Prompt (English):**
> gradients, soft shading, color transitions, lighting, ambient occlusion, drop shadows, cast shadows, ground shadow, blur, 3d render, bevel, highlights, particles, action lines, burst lines, floating icons, text, typography, letters, numbers, realistic details, sketch lines, watercolor, noise, grain, textures, dithering, busy background, complex patterns

**৪. Adobe Illustrator Trace Settings (Bengali):**
- Preset: Color (5 Colors), Noise: 15px, Paths: 80%, Ignore White: Checked.
```
