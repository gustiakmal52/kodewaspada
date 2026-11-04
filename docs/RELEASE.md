# Release checklist

Starting with **0.3.0**, KodeWaspada is open source under Apache-2.0. Releases before 0.3.0 retain the license files shipped with those releases; do not replace their artifacts or rewrite their tags.

## Source and attribution

Create release branches from the current public `origin/main`. The older development checkout may contain private material and unrelated changes: do not merge it into the public branch or use `git push --all` / `git push --mirror`.

1. Keep root `LICENSE` byte-identical to the official [Apache-2.0 text](https://www.apache.org/licenses/LICENSE-2.0.txt) and `skills/kodewaspada/LICENSE`.
2. Keep root `NOTICE` and `skills/kodewaspada/NOTICE` identical. Preserve the EL1Syum copyright and attribution, together with any applicable contributor notices.
3. Check that README, package metadata, product/scanner documentation, and release assets all describe the same version and license. A paid license is not required for commercial use of 0.3.0 or later under Apache-2.0.
4. Keep third-party components under their own licenses. Semgrep is installed separately; the release does not relicense or bundle the engine.

## Build and verify

Run the required checks from [AGENTS.md](../AGENTS.md), then record actual results in [QA.md](QA.md). Run independent behavioral evaluations from [evals](../evals/README.md) when skill behavior changes; a license-only update does not change the review instructions.

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q kodewaspada scripts
python3 /path/to/skill-creator/scripts/quick_validate.py skills/kodewaspada
python3 scripts/build_skill_bundle.py
python3 -m pip wheel . --no-deps --no-build-isolation --wheel-dir outputs/wheels
```

The skill builder requires Python 3.11+ and Linux/WSL. It enforces an exact file allowlist, canonical license/notice digests, safe output paths, and descriptor-based writes. It refuses existing outputs. Do not replace it with a manual ZIP command.

- Verify the ZIP CRC and SHA-256 sidecar, extract it to a temporary directory, compare every file against the skill source, and validate the extracted skill.
- Inspect the wheel metadata and its bundled `LICENSE` and `NOTICE`; install it in an isolated environment and run the CLI version check and negative-control scan.
- Publish only tracked source from the release commit. Exclude `.git`, secrets, private reports, caches, and previous build outputs.
- Create a new tag on the reviewed public commit, attach the tested artifacts, and download them again to verify their hashes. Record skipped checks honestly.

## Public wording

Describe KodeWaspada as an **open-source security-review skill for developers building with AI**, maintained by EL1Syum. Credit contributors and link to the repository.

Keep claims tied to observed results: fixture passes are not an accuracy percentage, security certification, or proof of production safety. Compatibility does not imply endorsement or official affiliation with OpenAI, Codex Security, or Daybreak.
