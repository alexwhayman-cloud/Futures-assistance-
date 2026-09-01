"""Daily morning brief: an AI team of one ChatGPT analyst per project.

For each repository the script gathers recent activity from the GitHub API,
asks the OpenAI API to analyse it (one "analyst" call per project), then a
final "editor" call compiles the combined brief, which is emailed via Gmail
SMTP and written to the workflow step summary.

Required environment:
  OPENAI_API_KEY      OpenAI API key
  MAIL_USERNAME       Gmail address used to send the brief
  GMAIL_APP_PASSWORD  Gmail app password (https://myaccount.google.com/apppasswords)
Optional:
  GH_PAT              GitHub PAT with read access to every repo below
                      (falls back to GITHUB_TOKEN, which only sees this repo)
  OPENAI_MODEL        defaults to gpt-5-mini
  MAIL_TO             defaults to alex.whayman@gmail.com
"""

import json
import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

import requests

REPOS = [
    "alexwhayman-cloud/Futures-assistance-",
    "alexwhayman-cloud/phuket-property-hub",
    "alexwhayman-cloud/cross-border-agency-platform",
]

BANGKOK = timezone(timedelta(hours=7))
OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-5-mini"
MAIL_TO = os.environ.get("MAIL_TO") or "alex.whayman@gmail.com"

GITHUB_TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN") or ""
GH_HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
}


def gh_get(path, params=None):
    resp = requests.get(
        f"https://api.github.com{path}", headers=GH_HEADERS, params=params, timeout=30
    )
    if resp.status_code in (404, 409):  # no access / empty repo
        return None
    resp.raise_for_status()
    return resp.json()


def gather(repo):
    """Collect recent activity for one repo; None if the token can't see it."""
    since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    commits = gh_get(f"/repos/{repo}/commits", {"since": since_24h, "per_page": 100})
    if commits is None and gh_get(f"/repos/{repo}") is None:
        return None
    window = "last 24 hours"
    if not commits:
        since_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        commits = gh_get(f"/repos/{repo}/commits", {"since": since_7d, "per_page": 100}) or []
        window = "last 7 days (nothing in the last 24 hours)"

    prs = gh_get(f"/repos/{repo}/pulls", {"state": "open", "per_page": 50}) or []
    issues = gh_get(f"/repos/{repo}/issues", {"state": "open", "per_page": 50}) or []

    return {
        "repo": repo,
        "commit_window": window,
        "commits": [
            {
                "sha": c["sha"][:7],
                "author": (c.get("commit", {}).get("author") or {}).get("name"),
                "date": (c.get("commit", {}).get("author") or {}).get("date"),
                "message": c.get("commit", {}).get("message", "").split("\n")[0],
            }
            for c in commits
        ],
        "open_pull_requests": [
            {
                "number": p["number"],
                "title": p["title"],
                "author": p.get("user", {}).get("login"),
                "draft": p.get("draft", False),
                "updated_at": p.get("updated_at"),
                "head": p.get("head", {}).get("ref"),
            }
            for p in prs
        ],
        "open_issues": [
            {
                "number": i["number"],
                "title": i["title"],
                "updated_at": i.get("updated_at"),
                "labels": [l["name"] for l in i.get("labels", [])],
            }
            for i in issues
            if "pull_request" not in i  # the issues API also returns PRs
        ],
    }


def openai_chat(system, user):
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


ANALYST_SYSTEM = (
    "You are a project analyst on a morning-brief AI team. Given raw GitHub "
    "activity for one repository, write a section of at most 10 lines with "
    "exactly three labelled parts:\n"
    "What changed: commits/PR movement in the stated window (or 'No changes').\n"
    "Status: one or two lines on where the project stands.\n"
    "Needed next: the 1-3 most important concrete actions.\n"
    "Be specific and terse; no preamble, no markdown headers."
)

EDITOR_SYSTEM = (
    "You are the editor of a daily morning brief for a solo developer. "
    "Combine the per-project analyst sections into one email body. Start "
    "with a 2-3 sentence overall summary across all projects, then each "
    "project section under a '== <repo name> ==' heading, unchanged except "
    "for light cleanup. Plain text only."
)


def main():
    missing = [
        v
        for v in ("OPENAI_API_KEY", "MAIL_USERNAME", "GMAIL_APP_PASSWORD")
        if not os.environ.get(v)
    ]
    if missing:
        sys.exit(f"Missing required secrets: {', '.join(missing)}")

    sections = []
    for repo in REPOS:
        data = gather(repo)
        if data is None:
            sections.append(
                f"{repo}: not reachable with the configured token — add a GH_PAT "
                "secret with read access to this repository."
            )
            continue
        section = openai_chat(
            ANALYST_SYSTEM,
            f"Repository: {repo}\nActivity window: {data['commit_window']}\n"
            + json.dumps(data, indent=1),
        )
        sections.append(section)
        print(f"analysed {repo}")

    today = datetime.now(BANGKOK).strftime("%A %d %B %Y")
    subject = f"Morning Brief — {today}"
    body = openai_chat(
        EDITOR_SYSTEM,
        "\n\n".join(
            f"=== {repo} ===\n{section}" for repo, section in zip(REPOS, sections)
        ),
    )
    body = f"{subject}\n\n{body}\n"

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(f"```\n{body}\n```\n")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.environ["MAIL_USERNAME"]
    msg["To"] = MAIL_TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(os.environ["MAIL_USERNAME"], os.environ["GMAIL_APP_PASSWORD"])
        smtp.send_message(msg)
    print(f"brief emailed to {MAIL_TO}")


if __name__ == "__main__":
    main()
