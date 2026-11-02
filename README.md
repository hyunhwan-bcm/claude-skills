# claude-skills

Skills for Claude Code, packaged as a plugin marketplace.

| Skill | What it does |
| --- | --- |
| [pdf-viewer](plugins/pdf-viewer/skills/pdf-viewer/SKILL.md) | Publishes a PDF (a slide deck, a paper, a report) as a claude.ai Artifact page that draws every page with PDF.js: arrow keys and swipe, section jumps from the PDF's bookmarks, a thumbnail strip, links to one page, and a switch between versions such as slides and slides with presenter notes. |

## Install

Pick one, depending on where you want the skill to work.

**As a plugin, on your machine** (needs git access to this repository):

```bash
claude plugin marketplace add hyunhwan-bcm/claude-skills
```

```bash
claude plugin install pdf-viewer@hyunhwan-skills
```

The skill then runs as `/pdf-viewer:pdf-viewer`, or by itself when you ask Claude to show a PDF as an artifact.

**As a personal skill, on your machine:** copy the skill folder.

```bash
cp -r plugins/pdf-viewer/skills/pdf-viewer ~/.claude/skills/
```

**In one repository:** copy the same folder to that repository's `.claude/skills/` and commit it.

**In cloud sessions (claude.ai/code) and Cowork:** these do not read `~/.claude/skills/` on your machine. Zip the folder and add it to the skills of your claude.ai account; skills enabled there load in cloud sessions, Cowork, and terminal sessions signed in to that account.

```bash
cd plugins/pdf-viewer/skills && zip -r pdf-viewer.zip pdf-viewer
```

## Use

Ask, for example: "Show `talk.pdf` as an artifact, with `talk-notes.pdf` as the notes version." The skill builds the page with `scripts/build_viewer.py`, checks it with `scripts/check_viewer.js` where Playwright is available, and publishes it with the Artifact tool.
