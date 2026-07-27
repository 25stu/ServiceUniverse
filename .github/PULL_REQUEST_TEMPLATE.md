## Purpose / 修改目的

- Team role:
- Service or shared component:
- Related Issue/contract:

Describe one focused outcome.

## Scope / 修改范围

- Owned paths changed:
- Shared paths changed:
- Known files intentionally not changed:

## Contract and integration impact

- [ ] No API/schema/activity-name change
- [ ] Backward-compatible change with contract updated
- [ ] Coordinated breaking change approved by affected owners and Leader

List endpoints, fields, statuses, errors, ports, or process activities changed:

## Verification

- [ ] `python -m ruff check .`
- [ ] `python -m pytest`
- [ ] `docker compose config`
- [ ] `docker compose up --build` when integration is affected
- [ ] `python scripts/smoke_test.py` when integration is affected
- [ ] UI screenshot attached when frontend is affected
- [ ] No secrets, `.env`, `.team-role`, database, or generated result committed

Paste relevant command results:

## Manual citizen workflow

State the start page, actions, and expected result used for manual verification.

## Known limitations

List unfinished or deliberately deferred work. Do not write “none” unless checked.

## Review

- Contract/service owner:
- Cross-reviewer:
- Leader review required: yes / no
