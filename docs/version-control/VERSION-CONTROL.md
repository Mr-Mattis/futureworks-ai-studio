# Version control and recovery scope

The initial baseline preserves reviewed source, contracts, synthetic checkpoint
evidence, governance records, Compose definition and the existing workflow export.
It does not certify that this export equals the current live n8n configuration.
The original source and locked governance/checkpoint files were not edited.
Only `.gitignore` and new version-control documentation are setup changes.

## Exclusions

Environment files (including existing templates), credentials, private keys,
local revision stores, n8n databases/volumes, backups, media, model weights,
caches and machine/tool state are excluded. Historical installation records and
synthetic table evidence are retained as evidence, not deployable runtime state.
Sample media remains on disk but is not included in Git. The README's environment
setup therefore needs a separately reviewed local template; no credentials should
be copied from a backup into version control. `.gitignore` cannot detect secrets
embedded inside otherwise eligible source files: review every future staged diff.

## Safe future changes

Use explicit file paths when staging. Check `git status`, `git diff`, and
`git diff --cached` before committing. Keep production changes separate and follow
the locked checkpoint process. A Git push only copies committed source; it does
not deploy, restart containers or run workflows. Never restore by resetting the
production directory blindly. Review a clone in a separate directory first.

## Backup verification performed at setup

Existing P00.07-20261110T041543Z backup: all 11 SHA-256 entries matched; database
opened immutable/read-only and `PRAGMA integrity_check` returned `ok`; four
workflow export objects; source tar archive readable. All 98 current contract
checksum entries matched. Backup files were not changed. This verifies saved
artifact integrity, not a production restore or freshness after November 10.
The backup includes sensitive material and must remain private and outside Git.

GitHub and the source-only Git bundle preserve the committed baseline, not n8n
credentials, database, later live workflow edits, revision-store contents or
media. A fresh production backup/restore test and automatic backups remain
separate operational work; none was performed as part of this task.

## Security review limits

Candidate text files were compared against secret values read locally from
existing environment/configuration files without printing those values; common
provider-token, JWT and private-key patterns were also checked. No matches were
found in the eligible files. This is a bounded review, not a guarantee against
all possible credential formats. No production tests or workflows were executed.
