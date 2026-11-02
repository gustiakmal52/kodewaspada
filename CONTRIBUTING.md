# Contributing to KodeWaspada

Thanks for taking the time to improve KodeWaspada.

The project prioritizes **evidence quality over warning volume**. A change is valuable when it helps the agent make a better security decision, especially when it reduces false positives or makes uncertainty clearer.

## Good contribution areas

- Add synthetic security fixtures with both vulnerable and safe controls.
- Improve guidance for authentication, authorization, tenant isolation, injection, XSS, SSRF, files/uploads, secrets, CI/configuration, or business logic.
- Add evaluation cases where the correct result is to dismiss a suspected finding.
- Improve cross-assistant compatibility documentation.
- Improve the optional scanner with a narrowly defined rule plus positive and negative tests.
- Improve documentation without overstating guarantees.

## Before opening a PR

1. Do not include client code, production data, credentials, real private vulnerability details, or proprietary fixtures.
2. Keep test data synthetic.
3. Preserve the distinction between source evidence, local-test evidence, and production behavior.
4. Do not turn scanner matches into automatic vulnerability claims.
5. If you change skill behavior, add or update an evaluation that demonstrates the intended decision.
6. If you add a scanner rule, include at least one positive and one negative fixture.

## Local checks

~~~bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q kodewaspada
~~~

Scanner-specific tests may require the Semgrep version documented in docs/SCANNER.md.

## What a useful report looks like

For behavior changes, explain:

- the scenario,
- the previous undesirable behavior,
- the expected decision,
- the synthetic fixture used,
- the actual result after the change,
- any known limitation that remains.

A reproducible narrow case is more useful than a broad claim such as "improves security."

## Security reports

Do **not** open a public issue for a vulnerability in KodeWaspada itself. Follow [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contribution may be distributed under the repository's existing PolyForm Noncommercial licensing terms and required notice. Review [LICENSE](LICENSE) before submitting a contribution.
