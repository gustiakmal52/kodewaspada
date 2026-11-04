# KodeWaspada contributor instructions

KodeWaspada is a source-available blue-team skill for coding assistants. Public use is governed by PolyForm Noncommercial 1.0.0; the copyright holder may separately offer paid commercial licenses. The primary product is `skills/kodewaspada/`; the Python/Semgrep scanner is optional supporting evidence for three JavaScript/TypeScript flows.

## Invariants

- Do not claim affiliation, endorsement, or official integration with OpenAI, Codex Security, or Daybreak. Compatibility with an Agent Skills format is not endorsement.
- Do not call the project open source while the PolyForm Noncommercial license applies. Preserve the exact root and bundled-skill license notices.
- Do not imply that a commercial inquiry, quote, or payment grants rights. Commercial permission requires a separate written agreement; keep `COMMERCIAL-LICENSING.md` consistent with that boundary.
- Do not merge external copyrightable contributions until the maintainer confirms an appropriate contributor agreement or relicensing grant. Issue reports and non-confidential feedback do not transfer code rights.
- Separate source evidence, local runtime evidence, and deployed-production evidence. Passing fixtures is not a scanner accuracy percentage or a security certificate.
- Findings must trace controllable input through validation/authorization to a sensitive operation and effect. Inspect controls that can disprove the hypothesis.
- Never add real credentials, client code, private reports, production data, or live-target probes to fixtures, issues, or commits.
- Review is read-only. A request to fix authorizes bounded local edits and tests, not deployment, publication, credential rotation, or external testing.

## Required checks

For scanner or packaging changes, run:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q kodewaspada scripts
python3 /path/to/skill-creator/scripts/quick_validate.py skills/kodewaspada
```

If the system validator path is unavailable, disclose that check as skipped; do not vendor it into this repo. Scanner integration tests require the separately installed Semgrep version documented in `requirements-engine.txt`.

For material skill-instruction changes, run the synthetic behavioral evaluations in `evals/README.md` with an independent agent that has not read the scoring criteria. Record actual outcomes in `docs/QA.md`; one passing evaluation does not establish cross-model accuracy.

Build shareable archives only with `scripts/build_skill_bundle.py`. It refuses to overwrite an existing artifact. Inspect the archive and its SHA-256 sidecar before distribution.

## Change discipline

- Preserve user changes and keep fixes scoped to the root cause.
- New scanner rules require a positive fixture and a negative control.
- New security logic requires a regression test. Do not silence findings or weaken tests to obtain a pass.
- Keep `README.md`, `README.id.md`, `COMMERCIAL-LICENSING.md`, `docs/PRODUCT.md`, `docs/SCANNER.md`, `docs/QA.md`, package metadata, and bundled license consistent with observable behavior.
