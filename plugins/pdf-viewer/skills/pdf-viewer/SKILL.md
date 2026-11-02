---
name: pdf-viewer
description: Publish a PDF as a claude.ai Artifact page that draws every page with PDF.js, for a slide deck (Beamer, PowerPoint or Keynote export), a paper, a poster or a report. The page pages through with arrow keys and swipes, jumps to sections from the PDF's bookmarks, shows every page in a thumbnail strip, links to single pages (#page-N), and can switch between versions such as slides and slides with presenter notes. Use when the user asks to show, share, present, view, draw or render a PDF in an artifact or as a web page.
---

# PDF viewer artifact

An Artifact page cannot embed a PDF: `<embed>`, `<object>` and iframes are blocked. This skill publishes the PDF as a file next to a page that draws it with PDF.js, so it looks exactly like the PDF.

## Steps

1. **Collect the PDFs.** Each must be at most 15 MB, all together at most 64 MB (Artifact limits). A deck can have a second version with presenter notes; for Beamer, build it with `\setbeameroption{show notes on second screen=right}`. Its pages are twice as wide, and the viewer handles that.
2. **Build the page.** Use the session's scratchpad for `--out` when it has one.

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/build_viewer.py --out <folder> --title "<Name>" \
     --pdf "Slides=<deck.pdf>" [--pdf "With notes=<deck-notes.pdf>"] \
     [--heading "<large text>"] [--subtitle "<one line>"] [--accent "#007948"]
   ```

   `--title` is the page's name in the browser tab and the gallery: two to four words, the thing's own name, no explanation after a colon. The first `--pdf` is shown first; two or more add a switch. The script refuses files that are not PDFs or are too large, and prints the `file_path` and `files` to publish.
3. **Check it** where Playwright and Chromium are available (Claude Code cloud sessions have both):

   ```bash
   node ${CLAUDE_SKILL_DIR}/scripts/check_viewer.js <folder> <page>.html --shots <folder>/shots
   ```

   It should print `"ok": true`: the first page drew, no page errors, no sideways scrolling at phone width. Look at the two screenshots once. Do not loop on it.
4. **Publish** with the Artifact tool, following its own rules for a first publish (it may ask for a quickstart call first). Pass `file_path` and `files` exactly as the build script printed them, `icon: "slides"` for a deck or `"document"` for anything else, and a one-sentence `description`. To update, rebuild into the same `--out` folder and publish the same `file_path`; the link stays the same.
5. **Tell the user** the link, that the page is private until they share it from its Share menu, and, if the PDF holds published figures or other people's material, to check its licence before sharing.

## How the page works

Keep these when editing `assets/viewer.html`; each one fixes a failure seen in testing.

- PDF.js 3.11.174 from cdnjs. The worker script is loaded as an ordinary `<script>`, so PDF.js runs on the page's own thread: an artifact page cannot start a worker from another host.
- `isEvalSupported: false`, because the page's security policy blocks `eval`. `disableRange` and `disableStream` fetch the whole file once.
- The current page draws first; thumbnails are queued and drawn one at a time as they scroll into view. Drawing them all at once delayed the first page by about five seconds.
- Section buttons come from the PDF's bookmarks (Beamer writes one per section). A bookmark that starts on the same page as its first child is skipped, which drops Beamer's empty "Appendix" entry.
- The section rail and the thumbnail strip scroll themselves, never the page; `.wrap > * { min-width: 0 }` stops the strip from widening the page on phones.
- Colours are tokens with light and dark themes. `--accent` sets the accent for both; the rest is neutral.
- The address follows the page (`#page-12`), so a link can open on one page.

## Limits

- Text is drawn, not selectable or searchable (no PDF.js text layer).
- The page cannot offer the PDF as a download (artifact pages block downloads); send the file separately.
- A PDF over 15 MB must be compressed first, for example `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -o small.pdf big.pdf`, then checked by eye: compression can blur figures.
