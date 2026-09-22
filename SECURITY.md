# Security policy

## Before publishing

- Never commit `config.local.bat`, `.env` files, database dumps containing production data, logs, private keys, or API tokens.
- Use `config.example.bat` only as a template. Keep actual database credentials in `config.local.bat`.
- Set a unique, high-entropy `JWT_SECRET` in `config.local.bat` before any shared deployment; rotate it if it was ever exposed.
- The bundled accounts are demonstration accounts only. Change or remove them before any non-local deployment.
- Review the question bank, images, and generated reports to ensure you have permission to publish them.

## Reporting a vulnerability

Do not open a public issue with exploit details or credentials. Contact the repository maintainer privately and include affected files, reproduction steps, and impact.
