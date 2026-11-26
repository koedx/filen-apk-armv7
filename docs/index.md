# Filen armv7 APK — spec index

Version: spec 15 · 2026-11-26T06:38Z

Read first each session: this file, then status.md.

Canonical copy: this `docs/` folder in koedx/filen-apk-armv7. The claude.ai Project "filen: armv7 apk" holds a mirror under `spec/`, updated in the same session as each commit.

| File | Covers |
|---|---|
| environment.md | Target device, constraints, network, tooling |
| build-ci.md | Repo, workflow, dispatch, ABI config, release assets, run history |
| crash-triage.md | Run 5 SIGSEGV (fixed in run 6, user-reported) — facts, root-cause candidate, ruled-out causes |
| delta-installer.md | Design and usage of the single-range delta installer (code in tools/delta/) |
| status.md | UNVERIFIED claims, open questions, next steps (ordered) |
| decisions.md | Append-only decision log |

Rules: topic files state the current design only and are edited in place. Every decision is one dated entry appended to decisions.md (what, why, supersedes). UNVERIFIED claims are marked where stated and listed in status.md. Timestamps UTC with Z.
