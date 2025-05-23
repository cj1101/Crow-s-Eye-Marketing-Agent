# Crow's Eye – Marketing Automation Platform (Full Feature Spec)

## 🧭 Overview
Crow's Eye is a smart marketing automation platform for creators and small businesses, focused on visual content for Instagram and Facebook. Its goal is to provide industry-best tools that *help creators survive now* — but ultimately become obsolete as people shift toward healthier media habits. This product is built with a critical lens on social media and should never contribute to mindless consumption.

---

## 🎨 Branding
- Company name: **Crow's Eye**
- Logo: Stylized black and purple crow's eye
- No tagline or motto — the mission is stated plainly in the product ethos

---

## 🧱 Folder Structure for Cursor (Web Version)

All code should follow this structure:

/components/ → All UI elements (cards, toggles, thumbnails, overlays)
/features/ → Core features (e.g., gallery generation, highlight reel logic)
/api/ or /backend/ → Server-side processing
/utils/ → Shared helper functions
/pages/ → Frontend page-level components (React)
/public/ → Static files

markdown
Copy
Edit

- Cursor must prompt if unsure about organization
- Code must stay modular and well-organized
- When implementing new features, generate code in the correct folder automatically

---

## 💡 Feature Set Breakdown

### 🟢 Free Tier

#### 📁 Media Library
- Upload raw media
  - Types: raw photos, raw videos, post-ready media (with captions/thumbnails)
- Auto-sort into 3 sections:
  - Raw Photos
  - Raw Videos
  - Post-Ready Posts (single, multi-image, or video w/ caption, CTA)
- Custom carousel builder from raw uploads

#### 🧠 Smart Gallery Generator
- Auto-generate galleries from selected raw media
- Natural language prompt support (e.g., "pick the best 5 for a winter campaign")
- Automatic photo enhancement (with toggle)
- Caption generation (auto, or user-guided with tone prompt)
- Manual override of all results

#### 📲 Post Formatting Options
- Post type selection:
  - Single image
  - Carousel
  - Story
- Story formatting:
  - Vertical optimization
  - Caption overlay as non-distracting text
- Interface Language Selection:
  - Mechanism: Accessible via a dropdown menu located in the main header, replacing the "Knowledge" button (the yellow button in the top navigation bar). The "Knowledge Base" button (the gray button at the bottom of the UI) will remain.
  - Behavior: Translates the entire user interface seamlessly into the selected language.
    - Affects all visible text elements.
    - Supported languages: Spanish, French, German, Dutch, Portuguese, Italian, Mandarin, Cantonese, Japanese, Korean, Russian (language selection labels displayed in their native form, e.g., "français").
  - Quality: The translation process should be quick, maintain UI design integrity, and ensure ease of use.

#### 🔍 Smart Media Search
- Search bar behaves like Google Photos
- Users can search media by content (e.g. "video with 2 people climbing")
- Also supports prompt-based filtering (e.g., "show only videos with motion blur")

---

### 💎 Pro Tier (Paid Features)
**Note: All features below are Pro-only. Priced at $5/month or usage-based.**

#### 🎞 Highlight Reel Generator
- User uploads a long video (e.g., 4 mins)
- System produces a highlight reel of user-defined length (default: 30s)
- Supports prompt input like:
  - "only show missed basketball shots"
  - "cut everything except crowd cheering moments"
- Downloadable result (desktop + web)

#### 🎧 Audio Importer
- UI element to upload audio (MP3, WAV, etc.)
- Audio editing (volume, tone, duration) controlled by natural language input
- Users **cannot upload audio via prompt** — file input only
- Supports overlays for Reels or Stories

#### 🎥 Story Assistant
- Takes long video + slices into <60s clips for Stories
- Formats vertically
- Adds overlays as needed (CTA, captions)
- Mobile-friendly download option (not auto-posting)

#### 🖼 Reel Thumbnail Selector
- After video generation, show auto-thumbnails + manual selector
- Optional custom upload

#### 📊 Post Performance Graphs
- Internal performance tracking
- Data source: user interactions, likes, shares, etc. (not Meta API)
- Export formats: CSV or JSON

#### 👥 Multi-User & Multi-Account
- Share media libraries and project workspaces
- Invite users via link
- Role-based permissions (admin/editor)
- Optional invite expiration

#### 🧮 Media Upload Limits
- **Unlimited uploads for desktop app**
- **Limited uploads for web version** (enforce via frontend)
- User prompted if exceeding free quota

---

## ⚙️ System Behavior & UI Expectations

### 🔄 Natural Language Prompts
- All promptable features must support text input
- Prompts examples:
  - "Show me 5 vertical photos from the beach"
  - "Generate a caption that sounds sarcastic but excited"
  - "Add 'tickets go live Friday' at the end of the video"
- UI must include fallback buttons and manual overrides

### 🎨 UI Requirements
- Adaptive text color overlays (white/black) based on contrast
- Light/noise UI design
- Smooth hover and transition effects
- Large tap targets (for mobile friendliness)
- Image/video previews are always shown before confirming post

---

## 🧪 Development Cycle Recommendations
- Finish full-featured desktop version first
- Then convert UI to React for web version
- Cursor to auto-organize all components as per structure
- Each new feature must include:
  - UI component
  - Prompt interpreter (if applicable)
  - Manual override
  - Result preview

---

## 📦 Deployment Plan
- Local desktop app (no hosting costs, no upload limits)
- Web version with login
- Stripe integration for paid tier (optional)
- Pricing model: $5/month or usage metering
- All core features remain free for desktop app users

---

## 🔐 Legal & Operational Notes
- Product built to be **acquired**, not scaled indefinitely
- Sole proprietorship in Texas (to minimize startup cost)
- If registered in the U.S., can operate globally under U.S. law
- Contractor agreements allowed, including F-1 visa holders under OPT with commission-based structure

---

## 🧠 Philosophy
> "This product is the best on the market *until people wake up*."

Crow's Eye is a tool for survival in a system that rewards inauthenticity. Our goal is not to entrench ourselves in that system, but to make it easier for creators to move through it — and eventually beyond it.

---