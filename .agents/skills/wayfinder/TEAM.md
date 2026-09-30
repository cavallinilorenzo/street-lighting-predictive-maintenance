# Team maps

A **team map** is a map on a repo with a **team doc** (`docs/agents/team.md`, written by `/setup-team`): **areas**, and the **members** who own each. On a team map every ticket has an **owner**, so the people splitting the map each work their own tickets instead of whichever is next in line. The team doc holds this repo's commands for everything below; on a team map they override the tracker doc's Claim and Frontier lines.

## Owner and claim

Two facts that a solo map folds into one assignee:

- **Owner**: who the ticket belongs to. The ticket's **assignee**, set when the ticket is created, plus an `area:<area>` label.
- **Claim**: who is working it right now. The `wayfinder:in-progress` label, added as the session's first write.

A ticket is **unclaimed** when it lacks `wayfinder:in-progress`, whoever owns it.

## Giving tickets owners

Whenever you create tickets (charting, or tickets surfaced while working), pick each one's area and an owner from the members of that area, and present them as one table: ticket name, area, proposed owner. Apply them once the user confirms.

- A HITL ticket's owner is the person who must speak for the decision: the grilling or prototype happens with them.
- A ticket that needs two areas' owners to decide is usually two questions. Propose the split; if it stays one ticket, the owner is whoever the decision hangs on, and the other joins the session.
- An area with several members: spread tickets between them, and say why each went where it did.

## Choosing the ticket

- **Named ticket**: owned by the driving dev or by nobody, claim it. Owned by someone else: say whose it is and ask before claiming, since a HITL ticket resolved without its owner has lost the human who speaks for it.
- **No ticket named**: take the first frontier ticket the driving dev owns; failing that, the first unowned one. Tickets owned by others stay off this dev's frontier.

## Team drift

On loading a team map, compare the tracker's collaborators with the team doc's members. When they differ (a collaborator with no area, a member who is no longer a collaborator, an owner who left), say so in one line and tell the user to run `/setup-team`. For open, unclaimed tickets whose owner has left or no longer covers the ticket's area, propose new owners in one table. Reassign only what the user confirms.
