# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.x (current) | ✅ |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing **curtis.franks@gmail.com** with:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Any suggested fix (optional)

You will receive a response within **72 hours** acknowledging receipt. We aim to release a patch within **7 days** of confirmation.

Once a fix is released, the vulnerability will be disclosed publicly via a GitHub Security Advisory.

## Scope

This policy covers the `receipts-api-mcp` codebase. The public GitHub Pages
dashboard at `https://chf3198.github.io/receipts-api-mcp/` is a client-side demo
that communicates only with a locally-run API instance — no server-side data is
stored or transmitted.

### In Scope

- Vulnerabilities in the FastAPI application (`src/receipts_api/`)
- Vulnerabilities in the MCP server integration (`fastapi-mcp`)
- Dependency vulnerabilities (`pyproject.toml` / `uv.lock`)
- GitHub Actions workflow vulnerabilities (`.github/workflows/`)
- GitHub Pages dashboard vulnerabilities (`docs/index.html`)

### Out of Scope

- Authentication and authorization hardening — the API is **intentionally
  public and read-only** by design. No auth is planned.
- Penetration testing of live infrastructure — no persistent server is
  deployed; the API runs locally only.
- Rate limiting / DDoS protection — out of scope for a local demo.

## Security Posture

A full Phase-0 security audit was completed on 2026-06-08 covering automated
scans, manual threat modelling, and an independent cross-family fleet red-team
review (`qwen2.5-coder:1.5b` @ OpenClaw — Qwen/Alibaba family, independent of
the Anthropic-family implementation author).

| Check | Result |
|---|---|
| `pip-audit` CVE scan | ✅ No known vulnerabilities |
| `detect-secrets` scan | ✅ No credentials in tracked files |
| ruff S (Bandit) rules | ✅ No actionable findings in `src/` |
| CDN SRI hashes | ✅ Chart.js 4.4.3 + PapaParse 5.4.1 integrity-verified |
| Dependabot | ✅ Enabled with automated security fixes |
| Fleet red-team (cross-family) | ✅ No P0/P1 findings confirmed |

**No P0 or P1 security findings were identified.**

### CORS Policy Rationale

```python
CORSMiddleware(app, allow_origins=["*"], allow_methods=["GET"])
```

The wildcard CORS policy is **intentional**:

- The API is public and **read-only** — no mutation, no state-changing methods
- **No authentication** — no cookies, no auth tokens, no sessions in scope
- Data is synthetic sample CSV — no PII, no sensitive information

Cross-origin access is required for the GitHub Pages dashboard to reach a
locally-running API instance. This would be a high-severity finding in a
production system with authentication.

### Data

All data served by the API is **synthetic sample data** (`assets/data/*.csv`).
No personally identifiable information, financial records, or credentials are
present in any file tracked by this repository.

## Branch Protection

The `master` branch is protected:
- Direct pushes blocked — all changes require a Pull Request
- CI checks (`test`, `presence-gate`) must pass before merge
- Stale PR approvals dismissed on new commits
- Force pushes and branch deletion blocked
