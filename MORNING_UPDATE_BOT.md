# Morning Project Update Bot

A scheduled Claude Code routine that delivers a daily morning brief covering
every active project, produced by a team of AI agents working in parallel.

## What it does

Every morning at **07:00 Bangkok time (00:00 UTC)** a routine named
**"Morning project brief"** fires and starts a fresh Claude Code session.
That session:

1. Attaches each project repository (read-only):
   - `alexwhayman-cloud/Futures-assistance-`
   - `alexwhayman-cloud/phuket-property-hub`
   - `alexwhayman-cloud/cross-border-agency-platform`
2. Launches one subagent per project, all running concurrently (the "AI team").
   Each agent reviews its repo: commits from the last 24 hours (falling back
   to the last 7 days if the day was quiet), open pull requests and their
   CI/review state, open issues, and unfinished work such as TODOs or
   failing checks.
3. Compiles the agents' reports into a single **Morning Brief** with, for
   each project:
   - **What changed** since yesterday
   - **Status** in one or two lines
   - **Needed next** — the 1–3 most important actions
4. Finishes, which sends a push notification and an email with the brief's
   summary. The full brief is the final message of the run's session,
   readable at [claude.ai/code](https://claude.ai/code).

The run is strictly read-only: it never pushes commits, opens or comments on
PRs/issues, or creates further schedules.

## Managing the routine

The routine lives in the claude.ai account (Routines), not in this
repository — this file is documentation only. From any Claude Code session
you can ask Claude to:

- **Pause / resume** — disable or enable the "Morning project brief" routine.
- **Change the time** — the schedule is a UTC cron expression (`0 0 * * *`);
  e.g. weekdays-only at the same hour would be `0 0 * * 1-5`.
- **Add or remove projects** — update the routine's prompt with the new
  repository list.
- **Delete it** — remove the routine entirely.

The same controls are available in the Routines UI on claude.ai.
