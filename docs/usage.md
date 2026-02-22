# Usage Guide

## Overview

ShotCut follows a simple 4-step workflow:

```
Upload Video → Annotate Marks → Extract Clips → Share
```

---

## Step 1: Upload a Video

You can add videos in two ways:

=== "Upload Local File"
    1. Go to the **Videos** page
    2. Click **Upload Video**
    3. Select an `.mp4` file (max 2GB by default)
    4. Wait for the upload to complete

=== "Import from YouTube"
    1. Go to the **Videos** page
    2. Click **Import from YouTube**
    3. Paste the YouTube URL
    4. Monitor download progress in real-time via the progress bar

---

## Step 2: Annotate Marks

1. Click a video to open the player
2. Press play and use keyboard shortcuts to mark moments:

| Key | Action |
|-----|--------|
| `1` | Offense |
| `2` | Defense |
| `3` | Turnover |

3. Each mark captures a ±5 second window around the keypress
4. **Drag timeline blocks** to fine-tune start/end timestamps
5. **Add player annotation** — click a mark and enter player numbers/names (e.g. `7 LeBron, 23 Jordan`)
6. Set playback speed: `0.25x` – `2x` for slow-motion review

---

## Step 3: Extract Clips

Once marks are set:

1. Select marks you want to extract (or select all)
2. Click **Extract Clips**
3. FFmpeg processes the clips in the background
4. Clips appear in the **Clips** list when ready

### Generate a Highlight Reel

Merge multiple clips into a single highlight video:

1. Go to **Highlights**
2. Choose filter: by **player** or by **category** (Offense / Defense / Turnover)
3. Click **Generate Highlight**
4. Download the merged video when complete

---

## Step 4: Share

1. Open a clip or highlight
2. Click **Create Share Link**
3. Choose expiry: **24h / 7d / 30d / Permanent**
4. Copy and send the link to coaches or parents

!!! info
    Recipients can view the video **without logging in** — no account required.

---

## Tips

- Use **slow-motion (0.25x)** to review contested plays frame by frame
- Use **2x speed** to quickly scan through long game footage
- Player annotations appear in the export filename, making it easy to sort highlights per player
- Share links expire automatically — no manual cleanup needed
