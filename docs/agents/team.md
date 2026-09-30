# Team

Who works on this repo and which areas each person owns. `/wayfinder` reads this to give every ticket an **owner**. Edit it by hand whenever the team changes, or re-run `/setup-team`.

## Areas

| Area       | Covers                                                                                                   |
| ---------- | -------------------------------------------------------------------------------------------------------- |
| `frontend` | Django templates, static assets, map/dashboard UI (`core/templates`, `core/static`)                       |
| `backend`  | Django models, views, URLs, migrations, settings; CSV import, management commands, sqlite DB             |
| `ml`       | Survival/risk models, training and prediction scripts, artifacts (`macchine learning/`, `ml_artifacts/`) |

## Members

| Handle                  | Areas    |
| ----------------------- | -------- |
| @itsmrma                | frontend |
| @cavallinilorenzo       | backend  |
| @TrentoElProgrammatores | ml       |

## Tracker operations

GitHub Issues on `cavallinilorenzo/street-lighting-predictive-maintenance`.

- **List collaborators**: `gh api repos/cavallinilorenzo/street-lighting-predictive-maintenance/collaborators --jq '.[].login'`. Pending invitations: `gh api repos/cavallinilorenzo/street-lighting-predictive-maintenance/invitations --jq '.[].invitee.login'`.
- **Area**: the label `area:<area>`. Create it with `gh label create "area:<area>" --force`.
- **Owner**: the ticket's assignee. `gh issue edit <n> --add-assignee <handle>`.
- **In progress**: the label `wayfinder:in-progress`. `gh issue edit <n> --add-label wayfinder:in-progress`.
