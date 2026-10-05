# Local Windows migration candidate — 2026-10-05

This report describes local candidates only. No remote branch, pull request,
release, repository permission or security setting was changed.

The candidate starts at py-dem-bones main `21797949b9fe0d425b35a390fddb553a9632b5d7`
(0.13.1), reuses PR #97 and the existing local configuration fix, and adds the
shared Windows CI builder. Its CLI source pin is msvc-kit
`8fefb7ffb21a624895fec6381d0f525f7fb9a335`, a local continuation of #176.
This pin must be uploaded to the official repository before remote CI can run.

## Official PR snapshot

Every listed py-dem-bones PR still had the existing Windows x64 CPython
3.8/3.9/3.10/3.11/3.12 release matrix at its inspected head. The reusable wheel
workflow accepts the same selectors. None had a native Windows ARM64 matrix.

| PR | Proposal | Observed checks | Required follow-up |
| --- | --- | --- | --- |
| #97 | Windows toolchain contracts | Windows/Linux/sdist pass; 9 macOS wheel jobs fail finding OpenMP | Continue with this candidate, latest main and the reused configuration fix |
| #91 | Black dependency | 7 failed wheel checks, including 3 Windows ABIs | Refresh onto the migration base, then rerun all wheels |
| #84 | setup-python v7 | No failed checks observed | Refresh onto migration base; retain its dependency change |
| #82 | github-script v9 | No failed checks observed | Refresh onto migration base |
| #80 | deploy-pages v5 | No failed checks observed | Refresh onto migration base |
| #79 | cache v6 | No failed checks observed | Refresh onto migration base; inspect cache action conflicts |
| #78 | checkout v7 | No failed checks observed | Refresh onto migration base; inspect the two checkout sites |
| #77 | configure-pages v6 | No failed checks observed | Refresh onto migration base |
| #72 | Python dependency | No failed checks observed | Refresh onto migration base; keep the wheel ABI matrix explicit |
| #64 | artifact actions | No failed checks observed | Refresh onto migration base; retain distinct ARM64 artifact names |
| #40 | cibuildwheel 2.23.4 | Observed build checks pass | Refresh onto migration base; configuration validation now follows the action's exact version |

msvc-kit has #176 (6 failed bundle/action checks caused by VSIX size metadata),
#175 (Tokio update; observed checks pass), and #164 (release proposal; no checks
observed). Apply the downloader/configuration continuation to #176 first.
Dependency #175 should then refresh onto that base. Leave #164's release decision
to its normal release process; this task does not merge or publish it.

Historical statuses were re-read: #94, #95 and #96 are merged. #95 merged at
2026-10-05 11:59:06 UTC and main is 0.13.1. The candidate preserves that version
and the sdist size guard from #96.

The heads and workflow matrices are recorded in `msvc-kit-pr-matrix.json`.
An end-of-validation read confirmed all listed heads and both main commits were
unchanged. Source check evidence was read directly from official GitHub APIs.

## Implemented behavior

All Windows CI wheel builds select msvc-kit: native x64 CPython 3.8–3.12 and
new native ARM64 CPython 3.11/3.12. Linux and macOS retain cibuildwheel and their
platform compilers. macOS explicitly selects the serial mode already intended
by #97; the corrected config-file/environment forwarding makes that setting
effective, instead of failing to find AppleClang OpenMP.

The action builds the pinned official CLI source with a locked Cargo dependency
set and Rust 1.93.1. It selects MSVC 14.44.35207, SDK 10.0.26100.0, VS17 and a
matching native host/target. Microsoft download hashes remain enabled. Both
acquisition receipts must exist before a per-run exact lock is passed to doctor
and query. Version/host/target mismatches fail before a wheel build.

Only download archives and their index are cached, keyed by source revision,
architecture and versions. Reuse rehashes bytes against the manifest. The
installed tree and extraction markers are excluded from the CI cache. The
builder explicitly selects cl/link/rc for Ninja, normalizes CMake paths, uses the
DLL CRT, and avoids the ccache launcher intended for GCC/Clang.

Wheel verification checks the CPython tag, every extension/DLL's PE architecture,
duplicate/unsafe entries and accidental compiler/debug files. Delvewheel bundles
runtime DLLs and omits diagnostics containing local paths. Portable summaries
contain versions, architectures and hashes, with no installation paths.

Failures propagate through subprocess exit codes and PowerShell checks. An
invalid explicitly selected CLI config now exits with failure instead of changing
to the default installation/cache root. The action writes a real TOML config.

## Completed local validation

| Check | Result |
| --- | --- |
| Fresh official VS17 manifest and four failing VSIX samples | All full SHA-256 values match; ZIP contents valid; manifest byte sizes differ |
| Rust downloader tests | 29 passed, including mutated cache, stale size, invalid digest, old index upgrade and disabled-verification boundaries |
| Rust library suite | 198 passed |
| Explicit-config CLI regression | Passed for both --config and MSVC_KIT_CONFIG; no default fallback |
| Rust format and all-target Clippy with warnings denied | Passed |
| Python configuration/ABI/content/failure contracts | 22 passed |
| Changed Python code lint and workflow actionlint | Passed |
| PyPI binary dependency resolution | Python 3.8 x64 and Python 3.11 ARM64 both pass; fixed delvewheel 1.10.0 / pytest-cov 5.0.0 support 3.8 |
| Toolchain acquisition | Compiler and SDK acquired and extracted in the isolated directory; 315 source payloads in the acquisition lock |
| Doctor probes | Compile, resource, link, manifest and native execution all pass |
| Real repaired wheel | 0.13.1, CPython 3.12 x64; every native PE entry matches x64 |
| Clean-environment installed wheel tests | 272 passed, 3 legacy computation skips; isolated import and one-bone tetrahedron reconstruction pass |
| Public wheel privacy scan | No local username, workspace path, user-profile path or host marker found, in text or native bytes |

The selected folder is 14.44.35207; CMake identifies the actual compiler as
MSVC 19.44.35229.0. The compiler bytes are hashed separately because a folder
version alone does not distinguish binary revisions. Exact compiler/wheel hashes
and bundled DLL names are in `msvc-kit-validation-evidence.json`.

The installed wheel test uses a fresh venv, isolated Python, no PYTHONPATH or
PYTHONHOME, and PATH restricted to that venv and System32. Its NumPy runtime
resolved to 2.5.3, while the build used NumPy 2.2.6. All numerical tests pass.

SDK administrative extraction encountered Installer contention during the local
attempt. Only this task's verified CLI/MSI client was stopped; the Installer
service and other tasks were left running. An absolute-directory retry and resume
completed successfully. CI always uses an absolute installation path.

## Remaining validation and remote sequence

1. Upload the reviewed msvc-kit continuation to a new branch or approved #176
   continuation without force pushing. The pinned CLI commit currently exists
   only locally. Run #176's bundle/action matrix, including x64→x86/ARM64.
2. Continue #97 with latest main, the existing config fix and this migration.
   Do not replace a moved remote head; merge/cherry-pick onto its current branch.
3. Run every Windows x64 ABI, both native ARM64 ABIs and the preserved Linux/macOS
   matrices. Native ARM64 compilation, OpenMP/runtime loading and numerical tests
   have not been executed locally. Dependency resolution is supporting evidence,
   not a substitute for those runs. macOS's corrected configuration still needs
   real AppleClang CI confirmation.
4. Once the migration is accepted on main, refresh #91/#84/#82/#80/#79/#78/#77/
   #72/#64/#40 onto that common base. This propagates one reviewed Windows builder
   to all open PR builds instead of maintaining divergent workflow copies.

The three skips are existing legacy computation tests that expect 2/3 weight
rows for rigid translations, receive one, and turn those shape assertions into
pytest.skip. They are a coverage gap, not successful fixed-count solver checks. The new
isolated numerical smoke and the non-skipping solve_skinning tests provide the
core reconstruction check. The Windows builder now reports skip reasons explicitly.

The acquisition lock records the exact bytes used by one run. Cross-run source
pinning beyond the exact CLI/toolset/SDK selections would require approved,
committed acquisition locks for each architecture; this candidate does not
pretend version directories alone are immutable binary digests.

No remote CI was dispatched in this task. No merge, force push, version release,
desktop interaction or global toolchain registration was performed.
