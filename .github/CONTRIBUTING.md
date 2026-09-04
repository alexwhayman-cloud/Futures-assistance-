# Contributing Guide

Thank you for your interest in contributing to Futures-assistance!

## Before You Start

1. **Check existing issues** - Search for similar issues before creating a new one
2. **Review the roadmap** - Understand project priorities
3. **Join discussions** - Ask questions in GitHub Discussions if uncertain

## Issue Types

### 🐛 Bug Reports
Use the **Bug Report** template when reporting defects. Include:
- Clear reproduction steps
- Expected vs. actual behavior
- Environment details (OS, version, component)
- Priority level

### ✨ Feature Requests
Use the **Feature Request** template for enhancements. Include:
- Clear problem statement
- Proposed solution
- Acceptance criteria
- Effort estimate

### 📋 Tasks & Work Items
Use the **Task** template for:
- Refactoring & tech debt
- Documentation updates
- Infrastructure/DevOps work
- Testing & QA

## Priority Levels

When creating an issue, select ONE priority:

| Priority | Definition | Example |
|----------|-----------|---------|
| **P0 - Critical** | Blocking production, security risk, data loss | API down, security vulnerability, data corruption |
| **P1 - High** | Major features broken, significant impact | Core feature fails, major bug affecting 50%+ users |
| **P2 - Medium** | Workaround exists, moderate impact | Feature partially broken, performance degradation |
| **P3 - Low** | Nice-to-have, cosmetic, edge cases | Typos, minor UX improvements, rare edge cases |

## Component Areas

Assign issues to component owners:

- **Frontend** - UI, UX, client-side logic
- **Backend** - API, services, business logic
- **DevOps** - Infrastructure, CI/CD, deployment
- **Documentation** - README, guides, API docs

## Issue Triage Workflow

1. **Submit** - Create issue with appropriate template
2. **Triage** (24h) - Assigned to component owner
3. **Estimate** - Estimate effort and dependencies
4. **Prioritize** - Assign to sprint or backlog
5. **Implement** - Developer picks up assigned issue
6. **Review** - PR review before merge
7. **Close** - Issue closed when PR merged

## Pull Requests

When submitting a PR:
1. Link the related issue: `Closes #123`
2. Reference priority label in description
3. Include component/domain in title
4. Provide context for reviewers

Example PR title: `[Backend] Fix authentication token refresh (P1 - Critical)`

## Communication

- **Questions?** Open an issue with the `question` label
- **Discussions?** Use GitHub Discussions tab
- **Security issues?** Report privately (see SECURITY.md)

---

**Questions?** Please open an issue or start a discussion. Happy contributing!
