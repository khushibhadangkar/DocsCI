# DocsCI

**DocsCI** is a production-grade docs-as-code quality and release-note automation CLI built in Python for technical writers, documentation engineers, and continuous integration pipelines. It automatically lints Markdown documents against pluggable style rules, organizational terminology lists, and front matter metadata standards; validates internal anchors and external hyperlinks with caching and polite rate limiting; aggregates Git Conventional Commits into lint-clean release notes; and optionally drafts customer-facing release summaries via the Google Gemini API protected by a two-way claim verification gate that prevents unverified claims from ever reaching production.

---

## 60-Second Quickstart

### 1. Installation

```bash
# Clone and create an isolated virtual environment
git clone https://github.com/example/DocsCI.git
cd DocsCI
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

### 2. Run Linting on Documentation

```bash
# Lint docs directory against style, terminology, and metadata rules
docsci lint docs/

# Strict mode: fail on warnings as well as errors in CI
docsci lint docs/ --strict
```

### 3. Check Hyperlinks and Heading Anchors

```bash
# Verify internal file paths, local anchors, and external URLs
docsci links docs/
```

### 4. Build Verified Release Notes

```bash
# Set Gemini API key (or omit to run completely offline via built-in mock client)
export GEMINI_API_KEY="your-gemini-api-key"

# Generate Conventional Commits release notes with verified AI summary
docsci release-notes --from v1.0.0 --to HEAD --ai-summary
```

### 5. Generate Documentation Health and Comparison Report

```bash
# Generate health metrics or compare against a previous audit
docsci report docs/ --previous baseline_report.json
```

---

## Sample CLI Output

### `docsci lint docs/`

```text
DocsCI Documentation Linting Report
================================================================================

📄 getting-started.md (2 violation(s)):
  [ERROR] L1:1     Missing required front matter field 'owner'. (front-matter-required)
          ↳ Fix: Provide a non-empty value for 'owner: ...'
  [WARN ] L14:1    Heading 'Initial Setup Guide' appears to use title case instead of sentence case. (sentence-case-heading)
          ↳ Fix: Consider: 'Initial setup guide'

--------------------------------------------------------------------------------
Summary: Scanned 14 file(s) | 1 error(s) | 1 warning(s) | 0 info
```

### `docsci release-notes --ai-summary` Verification Gate

```text
🤖 Generating AI release summary using prompt 'v1.0.0'...
🔍 Running claim verification audit against commit evidence...
✔ AI-assisted draft written to RELEASE_NOTES_DRAFT.md

Claim Verification Results: 3/3 claims supported.
  [SUPPORTED  ] Claim 1: Added immutable retention policies for S3 storage targets... (Evidence: 205e479)
  [SUPPORTED  ] Claim 2: Resolved connection timeouts during volume synchronization... (Evidence: 8fb31b7)
  [SUPPORTED  ] Claim 3: Updated role-based access control procedures... (Evidence: a1c9f40)
```

---

## Why a Human Accuracy Gate?

Generative AI introduces real efficiency gains for technical writers drafting release summaries, but Large Language Models are prone to critical failure modes:
1. **Hallucination**: Inventing features, protocols, or integrations not present in the code.
2. **Scope Inflation**: Exaggerating minor performance tweaks into 10x throughput breakthroughs.
3. **Stale Context**: Assuming obsolete architectural patterns from training data rather than actual codebase commits.

In enterprise data-security and backup environments, publishing inaccurate claims can lead to customer downtime, broken trust, and compliance breaches.

**DocsCI solves this with an architectural human accuracy gate:**
- Every AI summary is treated as an unverified draft and written to `RELEASE_NOTES_DRAFT.md` with an explicit warning banner: *"AI-assisted draft: requires human review. Never publish this draft automatically."*
- The verification engine splits the summary into atomic claims, parses the commit messages, and computes an evidence audit table.
- If even a single claim lacks corroborating commit evidence, the CLI exits with a non-zero exit code (`1`), halting automated pipelines unless `--allow-unsupported` is explicitly supplied.
- Output reproducibility is guaranteed by versioning prompts in `prompts/` and recording the exact prompt version in the draft metadata.

---

## Documentation and Resources

Comprehensive topic-based guides are located in the [`docs/`](docs/) directory:

- [Install Guide](docs/install.md): Prerequisites and environment setup.
- [Quickstart Guide](docs/quickstart.md): Step-by-step authoring walkthrough.
- [Configure Rules](docs/configure-rules.md): Rule options, severities, and link allowlists.
- [Add a Custom Rule](docs/add-custom-rule.md): Step-by-step tutorial with tested code (< 20 lines).
- [Terminology List](docs/terminology-list.md): Managing preferred terms and forbidden variants.
- [Release Notes Workflow](docs/release-notes-workflow.md): Conventional Commits changelog assembly.
- [AI Summary & Verification](docs/ai-summary-verification.md): Gemini client and claim verification engine.
- [Documented Failure Modes](docs/failure-modes.md): 5 real-world hallucination cases caught by the verifier.
- [Continuous Integration Setup](docs/ci-setup.md): GitHub Actions pull request and release workflows.
- [Troubleshooting](docs/troubleshooting.md): Common errors and solutions.
- [CLI Reference](docs/cli-reference.md): Complete options and arguments for every command.
- [Measurement Framework](MEASUREMENT.md): Empirical template for review time, diffs, and catch rates.
