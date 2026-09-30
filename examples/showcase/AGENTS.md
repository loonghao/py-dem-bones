# Native showcase contracts

- Use official host APIs through typed DCC-MCP tools first. If an official API
  exists but a DCC-MCP capability is missing, implement and validate it in the
  owning adapter repository and submit a PR.
- Use application UI automation only when the official API cannot express the
  operation. Use the project-owned `dcc-cua` / `ui-control` route. Report the
  provider, runtime version, target PID and HWND before observation or input.
  Do not fall back to generic Computer Use or browser automation.
- Keep native geometry, material binding, render completion and exported file
  validation as separate evidence. Never report pending or blocked host
  acceptance as completed.
- Publish complete native sequences with provenance and byte hashes. Preserve
  original frames; record display transforms and renderer-specific limits.
- Preserve user scenes and dirty checkouts. Use disposable case-owned state.
  Commit as `loonghao <hal.long@outlook.com>` with concise English Conventional
  Commits.
