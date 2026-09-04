# Issue Triage & Priority Runbook

**Purpose:** Define the process for reviewing, prioritizing, and assigning GitHub issues.

## Triage Schedule

- **Daily:** Review new issues (first thing each morning)
- **Weekly:** Sprint planning and backlog grooming (every Monday)
- **On-demand:** Emergency triage for P0/P1 issues

## Triage Workflow

### Step 1: Initial Review (24-hour SLA)
When a new issue arrives:

1. **Read completely** - Understand the problem/request
2. **Add type label** - `type: bug`, `type: feature`, `type: task`, or `type: question`
3. **Add component** - `component: frontend`, `backend`, `devops`, or `documentation`
4. **Check for duplicates** - Search for related issues
5. **Add initial notes** - Comment with clarifying questions if needed

**Status:** Add `status: needs-triage` label

### Step 2: Prioritization (48-hour SLA)
Assign one priority label:

| Priority | Decision Criteria | Assignment |
|----------|------------------|-----------|
| **P0 - Critical** | Blocks shipping, security risk, data loss | Owner + urgent attention |
| **P1 - High** | Major feature broken, high impact | Owner + next sprint |
| **P2 - Medium** | Workaround exists, moderate impact | Owner + planned sprint |
| **P3 - Low** | Nice-to-have, cosmetic, rare | Backlog, deprioritize |

**Assignment Logic:**
- **Frontend issues** → Frontend owner
- **Backend/API issues** → Backend owner
- **DevOps/Infra issues** → DevOps owner
- **Docs issues** → Tech writer or backend owner
- **Cross-component** → Primary owner + collaborate label

### Step 3: Estimation (Sprint Planning)
For issues selected for implementation:

1. **Add effort label** - `effort: xs`, `s`, `m`, `l`, or `xl`
2. **Add status** - `status: ready` when all info is complete
3. **Write AC** - Ensure acceptance criteria are clear
4. **Check deps** - Link blocking issues/PRs

## Owner Assignment Matrix

| Component | Owner | Backup |
|-----------|-------|--------|
| **Frontend** | [Team Member Name] | [Backup] |
| **Backend** | [Team Member Name] | [Backup] |
| **DevOps** | [Team Member Name] | [Backup] |
| **Documentation** | [Team Member Name] | [Backup] |

*Update this with actual team members*

## Priority Decision Tree

```
Is issue blocking production?
├─ YES → P0 (Critical) - Assign immediately
└─ NO
   ├─ Is it a security issue?
   │  └─ YES → P0 (Critical) - Assign immediately
   └─ NO
      ├─ Does it affect core functionality for >50% of users?
      │  └─ YES → P1 (High) - Assign to current/next sprint
      └─ NO
         ├─ Does it affect workflows or have moderate impact?
         │  └─ YES → P2 (Medium) - Schedule for backlog
         └─ NO → P3 (Low) - Add to nice-to-have backlog
```

## SLAs & Response Times

| Priority | Triage SLA | Assignment SLA | Fix SLA |
|----------|-----------|----------------|---------|
| P0 | 2 hours | 1 hour | 24 hours |
| P1 | 24 hours | 24 hours | 1 week |
| P2 | 48 hours | 3 days | 2 weeks |
| P3 | 1 week | Planning | Backlog |

## Labels to Apply During Triage

**Every issue gets:**
- One `type:` label (bug, feature, task, question)
- One `component:` label (frontend, backend, devops, documentation)
- One `priority:` label (critical, high, medium, low)
- One `status:` label (needs-triage → in-progress → needs-review → done)

**As needed:**
- `effort:` for sprint planning
- `good first issue` for onboarding
- `help wanted` for community involvement
- `security` for sensitive issues
- `duplicate` / `wontfix` / `blocked` for special cases

## Escalation Process

**If you cannot prioritize an issue:**
1. Add `status: needs-discussion` comment
2. Tag relevant stakeholders with @mention
3. Schedule 30-min sync to decide
4. Update issue with decision & reasoning

## Metrics to Track

- **Triage time:** Average time from creation → prioritization
- **Response time:** Average time from P1 creation → assignment
- **Fix time:** Average time from assignment → close
- **Open issues:** Total by priority (P0, P1, P2, P3)
- **Team velocity:** Issues closed per sprint

## Review & Iteration

- **Monthly:** Review triage efficiency metrics
- **Quarterly:** Adjust priority thresholds based on outcomes
- **As needed:** Add new label types or workflow improvements

---

**Questions?** Ask in #engineering or ping a maintainer.
