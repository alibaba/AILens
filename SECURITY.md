# Security Policy

## Reporting a Vulnerability

The AI-Lens team takes security seriously. If you discover a security vulnerability, please report it responsibly — **do not open a public GitHub issue**.

### How to Report

- **GitHub Security Advisories**: Open a private security advisory at the repository's Security tab → "Report a vulnerability"
- **Email**: Contact the maintainers with `[SECURITY]` in the subject line

### What to Include

- Clear description of the vulnerability
- Steps to reproduce
- Potential impact and scope
- Suggested remediation (if available)

### Response Process

1. Acknowledgment within 48 hours
2. Investigation and validation
3. Fix development and testing
4. Coordinated disclosure

## Supported Versions

Only the latest release and the `main` branch receive active security updates.

## Security Considerations

When self-hosting AI-Lens:

- Keep ClickHouse credentials out of version control — use environment variables or secrets managers
- Restrict ClickHouse network access to gateway service only
- The OTel Collector ports (4317/4318) should not be exposed to the public internet without authentication
- Keep all container images up to date
