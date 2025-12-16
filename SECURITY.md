# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Mizan seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email to [INSERT SECURITY EMAIL] with:

1. **Description**: A clear description of the vulnerability
2. **Impact**: What could an attacker achieve?
3. **Reproduction**: Steps to reproduce the vulnerability
4. **Affected versions**: Which versions are affected?
5. **Suggested fix**: If you have a suggested fix, please include it

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Updates**: We will provide updates on our progress
- **Timeline**: We aim to address critical vulnerabilities within 7 days
- **Credit**: We will credit you in the security advisory (if desired)

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version of Mizan
2. **Environment Variables**: Never commit `.env` files with real credentials
3. **Network Security**: Run the API behind a reverse proxy in production
4. **Database Security**: Use strong passwords and restrict database access

### For Developers

1. **Dependencies**: Regularly update dependencies
2. **Input Validation**: All user inputs are validated through Pydantic
3. **SQL Injection**: We use SQLAlchemy ORM to prevent SQL injection
4. **Secrets**: Never commit secrets to the repository

## Known Security Measures

### Input Validation

- All API inputs are validated using Pydantic models
- Arabic text is sanitized before processing
- Maximum text length limits are enforced

### Authentication (Future)

- API key authentication planned for production deployments
- Rate limiting to prevent abuse

### Data Protection

- The Quran text is read-only and cannot be modified
- Checksums verify text integrity
- No user data is collected or stored

## Vulnerability Disclosure Timeline

| Day | Action |
|-----|--------|
| 0 | Vulnerability reported |
| 1-2 | Acknowledgment sent |
| 3-7 | Assessment and fix development |
| 7-14 | Fix testing and release |
| 14+ | Public disclosure (coordinated) |

## Security Updates

Security updates will be released as patch versions (e.g., 0.1.1, 0.1.2) and announced in:

- GitHub Releases
- CHANGELOG.md
- Security Advisory (for critical issues)

---

Thank you for helping keep Mizan secure.
