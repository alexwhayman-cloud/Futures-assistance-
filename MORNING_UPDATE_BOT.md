# Morning Project Update Bot

A daily morning brief covering every active project — what changed, current
status, and what's needed next — produced by an AI team with one analyst per
project and emailed to you.

Projects covered:

- `alexwhayman-cloud/Futures-assistance-`
- `alexwhayman-cloud/phuket-property-hub`
- `alexwhayman-cloud/cross-border-agency-platform`

Both implementations below run every morning at **07:00 Bangkok time
(00:00 UTC)**.

## 1. GitHub Action — ChatGPT writes the brief (this repo)

`.github/workflows/morning-brief.yml` runs `scripts/morning_brief.py`, which:

1. Gathers activity per repo from the GitHub API: commits from the last
   24 hours (falling back to the last 7 days on quiet days), open pull
   requests, and open issues.
2. Runs the AI team: one OpenAI (ChatGPT) "analyst" call per project writes
   its *What changed / Status / Needed next* section, then an "editor" call
   compiles the combined brief with an overall summary.
3. Emails the full brief to you via Gmail SMTP and writes it to the
   workflow run's step summary.

### One-time setup (repo → Settings → Secrets and variables → Actions)

Secrets:

| Secret | Value |
| --- | --- |
| `OPENAI_API_KEY` | An OpenAI API key (platform.openai.com → API keys) |
| `MAIL_USERNAME` | The Gmail address that sends the brief, e.g. `alex.whayman@gmail.com` |
| `GMAIL_APP_PASSWORD` | A Gmail **app password** (myaccount.google.com/apppasswords — requires 2-step verification; your normal password will not work) |
| `GH_PAT` | A GitHub personal access token with **read** access to all three repos. Without it the workflow's default token only sees this repo, and the two private projects are skipped with a note in the brief. |

Optional variables: `OPENAI_MODEL` (default `gpt-5-mini`), `MAIL_TO`
(default `alex.whayman@gmail.com`).

Until the secrets are added, scheduled runs fail early with a clear
"Missing required secrets" message. Test any time from the Actions tab →
Morning Brief → **Run workflow**.

## 2. Claude routine — Claude's AI team (claude.ai account)

A routine named **"Morning project brief"** fires each morning and starts a
fresh Claude Code session that attaches all three repos, launches one
subagent per project in parallel, compiles the same three-part brief, and
sends a push notification plus a summary email when done. The full brief is
the run's final message at [claude.ai/code](https://claude.ai/code).

It lives in the claude.ai account (Routines), not in this repository. From
any Claude Code session you can ask Claude to pause/resume it, change the
schedule, add or remove projects, or delete it; the same controls are in the
Routines UI. To have the routine email the *full* brief from your own Gmail,
recreate it from the Routines UI with the Gmail connector attached.

Both channels are read-only with respect to your repositories: neither ever
pushes commits, opens or comments on PRs/issues, or modifies anything.

Once the GitHub Action is set up and delivering, you may want to pause the
Claude routine so you get one brief per morning, not two.
