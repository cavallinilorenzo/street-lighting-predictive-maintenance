# Team

Who works on this repo and which areas each person owns. `/wayfinder` reads this to give every ticket an **owner**. Edit it by hand whenever the team changes, or re-run `/setup-team`.

## Areas

| Area       | Covers                          |
| ---------- | ------------------------------- |
| `frontend` | UI, components, styling         |
| `backend`  | API, business logic, database   |

## Members

| Handle   | Areas              |
| -------- | ------------------ |
| @alice   | frontend           |
| @bob     | backend, frontend  |

## Tracker operations

GitHub shown; adapt to the repo's tracker (GitLab: project members, `glab issue update --assignee`; local markdown: an `Owner:` line in the ticket file).

- **List collaborators**: `gh api repos/<owner>/<repo>/collaborators --jq '.[].login'` (needs push access). Pending invitations: `gh api repos/<owner>/<repo>/invitations --jq '.[].invitee.login'`.
- **Area**: the label `area:<area>`. Create it with `gh label create "area:<area>" --force`.
- **Owner**: the ticket's assignee. `gh issue edit <n> --add-assignee <handle>`.
- **In progress**: the label `wayfinder:in-progress`. `gh issue edit <n> --add-label wayfinder:in-progress`.
