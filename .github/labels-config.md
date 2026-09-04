# GitHub Labels Configuration

This document defines the label taxonomy for issue organization and triage.

Run the following to create these labels via GitHub CLI:

```bash
# Priority Labels
gh label create "priority: critical" --description "P0 - Blocking production, security, data loss" --color "ff0000"
gh label create "priority: high" --description "P1 - Major features broken, significant impact" --color "ff5500"
gh label create "priority: medium" --description "P2 - Moderate impact, workarounds exist" --color "ffaa00"
gh label create "priority: low" --description "P3 - Nice-to-have, cosmetic, edge cases" --color "ffff00"

# Type Labels
gh label create "type: bug" --description "Something isn't working" --color "d73a49"
gh label create "type: feature" --description "New feature or enhancement" --color "a2eeef"
gh label create "type: task" --description "Work item (refactor, docs, ops)" --color "cfd3d7"
gh label create "type: question" --description "Question or discussion needed" --color "d4c5f9"

# Component Labels
gh label create "component: frontend" --description "UI, UX, client-side" --color "0075ca"
gh label create "component: backend" --description "API, services, business logic" --color "1f883d"
gh label create "component: devops" --description "Infrastructure, CI/CD, deployment" --color "62220e"
gh label create "component: documentation" --description "README, guides, docs" --color "0E8A16"

# Status Labels
gh label create "status: needs-triage" --description "Needs review and prioritization" --color "cccccc"
gh label create "status: in-progress" --description "Actively being worked on" --color "0366d6"
gh label create "status: blocked" --description "Blocked by another issue" --color "b60205"
gh label create "status: ready" --description "Ready for implementation" --color "28a745"
gh label create "status: needs-review" --description "Awaiting code review" --color "fbca04"

# Effort Labels
gh label create "effort: xs" --description "Extra small (< 2 hours)" --color "c2e0c6"
gh label create "effort: s" --description "Small (2-4 hours)" --color "bfdadc"
gh label create "effort: m" --description "Medium (half day)" --color "bfe5bf"
gh label create "effort: l" --description "Large (full day+)" --color "ffeaa7"
gh label create "effort: xl" --description "Extra large (multiple days)" --color "ffcccc"

# Special Labels
gh label create "good first issue" --description "Good for newcomers" --color "7057ff"
gh label create "help wanted" --description "Help from community appreciated" --color "33aa3f"
gh label create "wontfix" --description "Will not be fixed" --color "ffffff"
gh label create "duplicate" --description "Duplicate of another issue" --color "cccccc"
gh label create "security" --description "Security related" --color "ff0000"
```

## Label Usage

### Priority
- Assign **one** priority label per issue
- Use Critical/High for backlog grooming
- Low/Medium for nice-to-have work

### Type
- Assign **one** type label per issue
- Helps categorize and filter work

### Component
- Assign **one or more** component labels
- Helps route to correct owner
- Use for cross-functional work

### Status
- Assign workflow status as it progresses
- Update on regular cadence

### Effort
- Assign after estimation meeting
- Used for sprint capacity planning

### Special
- Apply as needed (security, duplicates, etc.)
