# GitHub Actions

| Workflow | Purpose |
| --- | --- |
| `lint.yml` | Check Python style and formatting. |
| `docs.yml` | Build and publish documentation. |
| `release.yml` | Build/test packages on PRs; publish artifacts and PyPI package for a `vX.Y.Z` tag. |
| `release-please.yml` | Open a version/changelog PR from Conventional Commits on `main`; create tag and GitHub Release after that PR merges. |
| `version-consistency.yml` | Check all release-please-managed version files against the manifest. |

See [the release guide](../../docs/ci_cd.rst) for the sequence, token requirement, and package publication contract. Do not manually bump version files for a normal release.
