# Windows migration review and rollout, 2026-10-05

The fixed local review inputs were msvc-kit
`4f6ff42cdc714f9831821711aeba1c2ae9a43f43` and py-dem-bones
`aba267be7f6368331356a174b4a340066a6811ce`. Source and adversarial regression
review found integrity/configuration blockers in the CLI. The follow-up fixes
are described in msvc-kit's `docs/guide/integrity-review-2026-10-05.md`.
This review does not constitute a separate reviewer's approval.

The Windows action now pins corrected CLI source
`b6d38e423e2eda25d47851ba03db4c062272f69e`. Its 199 library tests, 4 manifest
integrity fixtures, 2 explicit-config tests, 3 config-creation compatibility
tests and warnings-denied Clippy checks passed. The Python configuration/wheel
contract suite passed 22 tests and all three modified workflows passed actionlint.
The freshly built CLI exited 1 for the official manifest SHA discrepancy below.
The later CLI fixture correction passed its two integration tests and changes
no production Rust code from the tested integrity commit
`5dd2d2ccd7329cbcd001ef2084f723b1fbe79389`.

## Integrity gate

Microsoft's fresh VS17 channel declares package manifest SHA256
`6e470016e4324c84c255ffd0beb3767d17ec89cc8561e9409ee3e1f6d29400f5`.
The official download URL returns
`f0a50ea157222c29abd5ea6ff01bfc3c33b04e011c5e45ee2ca38ef0778e5643`.
No-cache/identity-encoding and cache-bypass retries reproduced this discrepancy.
The strict CLI rejects it before parsing, extracting, or creating acquisition
receipts. The Windows action keeps hash verification enabled and must fail on
this input. Do not merge or substitute a locally computed digest for the
official expected value to make CI green.

The prior x64 CPython 3.12 wheel passed a clean installation, isolated import,
numerical reconstruction, and 272 runtime tests. Three legacy shape assertions
were caught and skipped by existing tests, as recorded in the validation report.
Those skips remain coverage gaps. That functional result predates the strict
channel-to-manifest SHA check and does not certify new acquisition or the entire
Windows ABI matrix. Native x64 CPython 3.8–3.12 and ARM64 3.11/3.12 must complete
their actual wheel build/install/import/numerical jobs before merge.

## Existing release and macOS runner changes

The existing 0.13.1 release completed successfully at 2026-10-05 12:17:12 UTC:
<https://github.com/loonghao/py-dem-bones/actions/runs/37306505059>.
Official PyPI metadata lists 20 files; the sdist is 3,303,273 bytes, SHA256
`16725de0c5b9c04fb28adaede1f0341870aca637bd64875ea16db43048eb1305`.
The earlier oversized 0.13.0 sdist is historical, not an unresolved blocker for
the current published version. This work does not publish another release.

The macOS ARM release job moves from `macos-14` to `macos-15`. GitHub announced
brownouts starting 2026-10-05 14:00 UTC through 2026-10-06 00:00 UTC and retirement
on November 2: <https://github.com/actions/runner-images/issues/13518>.
GitHub's runner reference identifies `macos-15` as ARM64 and `macos-15-intel` as
Intel: <https://docs.github.com/en/actions/reference/runners/github-hosted-runners>.
The Intel job remains `macos-15-intel`; ARM selectors remain cp39/cp310/cp311/cp312
and `macosx_arm64`. Linux/macOS continue using their platform compilers and
cibuildwheel. The runner move requires its own CI evidence; a brownout failure
must not be reclassified as a passing required check.

## First approved CI run and configuration correction

The first #176 continuation run failed acquisition with the same declared and
retrieved manifest SHA values observed locally. Rust/coverage also exposed an
older CLI test fixture that wrote an empty, schema-invalid TOML file. Its fixture
was corrected to serialized valid isolated settings; the production invalid
configuration check remains strict.

The first #97 run reached cibuildwheel on Linux and both macOS architectures,
but ccache rejected the now-effective legacy `CCACHE_BASEDIR="{package}"`.
Command placeholders are not expanded in environment table values. Linux now
uses the container's absolute `/project` source directory, macOS resolves `$PWD`
from the actual job environment, and the unused Windows cibuildwheel cache base
is empty. Effective-configuration regressions verify those resolved values.
No platform compiler, OpenMP policy, ABI selector or integrity check is changed
by this correction. The observed failures require a fresh CI run on the new head;
they were configuration failures rather than a macOS runner brownout.

The corrected Linux/macOS run built and installed its native wheels, then
exposed nox's runtime pytest invocation discovering orchestration tests outside
the runtime directory: `--rootdir` does not restrict test discovery. The runtime
invocation now passes the test directory explicitly; the separate effective
configuration CI step continues to execute its pinned-tool orchestration suite.
Local execution of the explicit runtime directory passed 272 tests with the same
three documented legacy shape skips. No tests are newly skipped or removed.

## Complete open PR coverage

The original heads and parsed source matrices are in `msvc-kit-pr-matrix.json`.
A fresh read during review confirmed all 14 heads below remained unchanged.
All eleven py-dem-bones PRs currently carry x64 cp38/cp39/cp310/cp311/cp312 and no
native Windows ARM64 job. The common migration supplies the native ARM64 matrix.

| Repository / PR | Reviewed remote head | Follow-up |
| --- | --- | --- |
| msvc-kit #176 | `2736536755659e5f18c064c5d2d5bcc46c3c3e19` | Approved continuation; ordinary fast-forward push, new CI and independent review; integrity gate blocks merge |
| msvc-kit #175 | `6751e097d784d1ebf2dcd50115d56dd202e28b5a` | After #176 lands, refresh its base and rerun Rust/action CI; no duplicate workflow migration |
| msvc-kit #164 | `2797077242263dd689f67d9a4721d38e813c6e4b` | Release-please should refresh its proposal after landing; normal release checks; no merge, tag or publication authorized here |
| py-dem-bones #97 | `7c80520b6325aeaeb53dc5ffc5232dcb2d1859f8` | Approved continuation; merge local migration/latest main into existing PR ancestry; new full platform CI and independent review |
| py-dem-bones #91 | `f8df47eeeaf447b01cfc19a2f7212659aef0caac` | Refresh base after #97 and rerun all wheels/lint; previous seven wheel failures include three Windows ABIs; retain Black change |
| py-dem-bones #84 | `13f6e2895a53033f8ab28e007da118e8fe5d322a` | Refresh base and rerun matrix; reconcile setup-python dependency change across the new Windows composite |
| py-dem-bones #82 | `66bb53ec167933552b4af52a240a25340da3653a` | Refresh base and rerun existing CI; retain github-script dependency change |
| py-dem-bones #80 | `bd79dade647dd24e8820f4fb8742f3280cf2182a` | Refresh base and rerun existing CI; retain deploy-pages dependency change |
| py-dem-bones #79 | `ff745ad49806b82e9627be05e9ddff88b1eba05e` | Refresh base and rerun matrix; reconcile cache version references without caching installed toolchain trees |
| py-dem-bones #78 | `04a9336e9c4e00f5012282c2495ccba99972e924` | Refresh base and rerun matrix; reconcile both project and CLI-source checkout references |
| py-dem-bones #77 | `a49b3a0f20d544eaced51b4ab6590cd19a245b69` | Refresh base and rerun existing CI; retain configure-pages dependency change |
| py-dem-bones #72 | `b2624c4f792b8a3ae5f116ea7b7d59dd6845870a` | Refresh base and rerun matrix; preserve explicit native interpreter/ABI pairs when updating Python tooling |
| py-dem-bones #64 | `09269e9efa2a202e6f0aa93d1c9d3cb8c11d9706` | Refresh base and rerun matrix; reconcile artifact action versions while retaining distinct Windows ARM64 artifact names |
| py-dem-bones #40 | `3ee59efe0de9103f48f9246dc95bfdd6fe040aa7` | Refresh base and rerun non-Windows config/wheels with cibuildwheel 2.23.4; config validator follows the action version; Windows retains msvc-kit |

The ten py-dem-bones dependency PRs need the common base, not ten copies of the
Windows workflow patch. Existing green checks on their old heads do not validate
the new base. Other PRs are listed for analysis only and will not be modified by
this approval. #94/#95/#96 are merged; #95 released 0.13.1 and #96 reduced the
sdist. They need no repeated workflow changes.

## Safe push and merge conditions

Fetch the official branch immediately before pushing and require its old head
to remain an ancestor of the intended new head. #176 is a direct continuation.
For #97, merge the local candidate into a branch starting at its existing remote
head so the earlier PR commit and current main are retained. If either remote
head changes, reconcile and repeat affected validation; never force-push.

Only #176 and #97 may be pushed or merged under this approval. They remain drafts
while the integrity gate is unresolved. No release/tag, repository security
setting, unrelated branch or global toolchain is changed. Required CI, all real
Windows ABI jobs, preserved Linux/macOS jobs and independent review must pass
on the final PR heads before a merge.
