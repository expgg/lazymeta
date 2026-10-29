---
name: lazymeta-vector-prompt-engine
description: Generate ultra-precise, high-hook editorial 2.5D vector image prompts for Google AI Flow, Imagen 3, Midjourney, or Flux, mapped directly to LazyMeta 30-day queues (01.jpg - 90.jpg) with zero Illustrator trace overhead.
---

# LazyMeta High-Hook Visual Prompt Engine (v3.0)

Use this skill to generate **thumb-stopping, high-retention 2.5D editorial vector prompts** that publish directly to Meta feeds without any Adobe Illustrator image-trace bottleneck.

---

## 1. Core Production Pipeline

```text
Post Topic / captions.txt
        │
        ▼
[This High-Hook Prompt Engine]
        │
        ▼
Google AI Flow / Imagen 3 / Midjourney / Flux
(Edgy 2.5D Vector, Obsidian Backdrop, Dual-Tone Rim Light)
        │
        ▼
images/01.jpg ... images/90.jpg  (Direct Save)
        │
        ▼
LazyMeta Bulk Scheduler (python run.py schedule)
```

* **No Adobe Illustrator Trace:** Images drop straight from the AI generator into `images/` without manual tracing or path expansion.
* **No Pure White Cutouts:** Flat `#ffffff` backgrounds look like generic clipart. We use deep obsidian `#0B0F17` atmospheric backdrops that make visuals violently pop in mobile dark and light feeds.

---

## 2. The 0.3-Second Scroll-Stop Architecture

Mobile feed users judge the image before reading any text. To halt the scroll:

1. **Visual Irony / Metaphorical Tension:** Don't depict someone passively typing at a desk. Depict tension: a tiny developer debugging a colossal monolith; a scale where 1 clean line of code outweighs 10,000 messy lines; a lone consultant flipping a single lever that powers an entire factory.
2. **Focal Simplicity (Low Cognitive Load):** Exactly **1 or 2 dominant focal elements**. The visual punchline must be grasped in under 200 milliseconds.
3. **Dual-Tone Volumetric Rim Lighting:** Neon electric cyan + hot orange, or emerald green + violet, carving out razor-sharp edges against dark slate.
4. **Anti-AI Craftsmanship:** Enforce vector contours, stylized faceless silhouettes, and geometric 2.5D glassmorphism. Suppress waxy plastic skin, uncanny valley faces, and distorted hands.
5. **Micro Tech Badges:** Include a single sharp UI pill tag (e.g. `STATUS: 200`, `v2.4`, `API DEPLOYED`, `LEVERAGE: 10X`) to anchor credibility.

---

## 3. Communication Protocol

* **Operator Interaction:** Communicate with the user strictly in **English**.
* **Post Captions (If Farming Bengali Audience):** Provide Bengali post text if requested, but all **Main Prompts** and **Negative Prompts** MUST be written in **English** for maximum AI image fidelity.
* **Queue Tagging:** Always tag the exact file mapping (`images: 01.jpg`, `images: 02.jpg`, etc.).

---

## 4. Prompt Template

```markdown
### 🖼️ Post [XX] -> `images: [XX].jpg`

**Visual Hook Concept:**
[2-line explanation of the visual metaphor, conflict, and scroll-stopping reason]

**Main Image Prompt (English):**
> High-end editorial vector illustration, modern 2.5D tech graphic with dramatic cinematic lighting, [1:1 square / 4:5 portrait] aspect ratio. [CENTRAL METAPHOR & TENSION: e.g. A stylized silhouette developer standing at the edge of an immense floating dark-slate server monolith, reaching toward a single glowing neon-emerald circuit switch]. Clean geometric silhouettes, rich color depth, sharp vector boundaries with translucent frosted-glass floating UI elements. Minimal sharp UI badge in top corner reading '[MINIMAL BADGE: e.g. STATUS: 200]'. Atmospheric deep obsidian navy background (#0B0F17) with faint subtle blueprint grid lines and glowing vector particles. High-contrast dual-tone volumetric rim lighting in electric cyan and warm amber accentuating the subject contours. Masterpiece digital art, sleek Linear and Stripe editorial tech design aesthetic, hyper-clean vector shapes, zero noise, high visual hook retention, aspect ratio [1:1 / 4:5].

**Negative Prompt (English):**
> photorealistic human face, realistic skin texture, ugly plastic AI look, distorted hands, blurry lines, low quality, chaotic cluttered background, unreadable messy gibberish text walls, 3d clay render, cheesy cartoon, stock photo, watermark, washed out colors, flat boring white background
```

---

## 5. Few-Shot High-Hook Examples

### Example 1: High-Stakes Code Architecture
* **Visual Hook:** A lone developer in dark technical streetwear holding a single warm-amber glowing key before a giant translucent glass monolith filled with glowing circuit nodes.
* **Main Prompt:**
  > High-end editorial vector illustration, modern 2.5D tech graphic of code architecture, 1:1 square aspect ratio. A sleek stylized silhouette developer standing on a clean floating dark-graphite platform, holding a glowing warm-amber key toward an immense translucent glass cube containing glowing circuit nodes and wireframe geometry. A sharp frosted glass badge floats beside it reading 'CORE LOGIC'. Atmospheric deep obsidian background (#0A0E17) with faint geometric coordinate lines. Dramatic cinematic dual-tone rim lighting in electric cobalt blue and vibrant gold outlining the character and glass edges. Clean vector contours, Stripe Press and Linear design aesthetic, visually striking thumb-stopper composition, aspect ratio 1:1.
* **Negative Prompt:**
  > realistic face, plastic 3d render, blurry, generic stock photo, messy text walls, ugly hands, chaotic composition, washed out lighting, flat plain white background

### Example 2: The Leverage Principle (Business / Consulting)
* **Visual Hook:** A consultant calmly pressing a single cyan button that engages massive dark-slate precision gears, representing output leverage.
* **Main Prompt:**
  > High-end editorial vector tech illustration depicting leverage versus brute force, 1:1 aspect ratio. Central composition features a stylized faceless professional in side profile wearing a sharp dark blazer, calmly pressing a single glowing neon-cyan power switch on an elegant floating console. In the background, massive interconnected dark-slate mechanical gears and glowing translucent data pipes power up in synchrony. A crisp, sharp status badge reads 'LEVERAGE: 10X'. Deep midnight navy backdrop with subtle ambient light leaks and fine vector measurement lines. Electric cyan and vibrant coral volumetric rim lighting creating extreme edge contrast. Masterpiece vector art, modern tech editorial style, ultra-high engagement visual hook, aspect ratio 1:1.
* **Negative Prompt:**
  > photorealism, blurry, cheesy 3D, noise, low resolution, crowded unreadable text, dull flat colors, stock photo, plain white background
