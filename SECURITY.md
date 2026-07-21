# Security Policy

## Reporting a vulnerability

Do not open a public issue for vulnerabilities, leaked credentials, gateway URLs, or authentication problems. Report them through the team's private security channel and include the affected version, reproduction steps, and impact.

## Credential handling

- Never commit `.env`, API keys, access tokens, generated credentials, or production gateway URLs.
- Each user must use their own `XAI_HASHMICRO_API_KEY`.
- Review release archives before distribution.
- Rotate a credential immediately if it appears in Git history, logs, screenshots, issues, or chat.

## Supported version

Security fixes are applied to the latest released version. Older local builds should be upgraded before troubleshooting.

