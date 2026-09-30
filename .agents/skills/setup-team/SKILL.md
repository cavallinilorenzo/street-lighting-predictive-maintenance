---
name: setup-team
description: Record who works on this repo and which areas each person owns, so /wayfinder gives every ticket an owner. Re-run whenever the team changes.
disable-model-invocation: true
---

# Setup Team

Write this repo's **team doc**: the **areas** the work splits into (frontend, backend, infra, whatever fits), and the **members** who own each one. `/wayfinder` reads it to give every ticket an **owner**, so a team can split a map between people instead of each session taking the next ticket in line.

The team doc routes work; it doesn't enforce it. Every collaborator on a personal repo can still touch everything. Enforcement belongs to the tracker (branch protection, required reviews), not to a skill.

The issue tracker should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`. A team needs a tracker every member can see: on the local-markdown tracker, the team doc only works if `.scratch/` is committed and shared.

Run it the first time the team forms, and again whenever someone joins, leaves, or changes area. Editing `docs/agents/team.md` by hand works just as well.

## Process

### 1. Explore

- The tracker doc: which tracker, which repo.
- `docs/agents/team.md`: present means this is a **re-run**.
- The repo's **collaborators**, and any pending invitations (see the tracker operations in [team.md](./team.md)). A pending invitee can't be assigned until they accept.
- Existing `area:*` labels on the tracker.
- The repo's top-level layout (`web/`, `api/`, `infra/`, a monorepo's packages): a hint for which areas the work already splits into.

Done when you hold the collaborator list, the current team doc (if any), and a candidate list of areas.

### 2. Agree the areas

Propose the areas in one message: from the existing team doc on a re-run, otherwise from the labels and the layout. One line each on what the area covers. Keep them coarse: an area is a slice of ownership, not a module. Done when the user has confirmed the list.

### 3. Assign the members

- **First run**: a table of every collaborator with your proposed areas. A member may own several areas; every area needs at least one member.
- **Re-run**: show only the **drift** between the collaborators and the team doc: who is new (needs areas), who is gone (remove them?), and any area now left with nobody. Then ask whether anything else changes.

Done when every collaborator has at least one area or has been deliberately left out, and every area has a member.

### 4. Confirm and write

Show the draft of `docs/agents/team.md`, built from [team.md](./team.md) with the tracker operations adapted to this repo's tracker. Let the user edit, then write it.

On the tracker, create an `area:<area>` label for every area, plus `wayfinder:in-progress`. Leave labels of removed areas in place unless the user asks: open issues may still carry them.

Add a `### Team` sub-block to the `## Agent skills` block in whichever of `CLAUDE.md` / `AGENTS.md` holds it, updating it in place on a re-run:

```markdown
### Team

[one-line summary: how many members, which areas]. See `docs/agents/team.md`.
```

### 5. Done

Tell the user what changed. On a re-run where someone left or changed area, add that `/wayfinder` proposes new owners for their open tickets the next time it loads a map; nothing is reassigned until they confirm.
