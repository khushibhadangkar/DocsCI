---
title: AI summary and verification
description: How DocsCI generates summaries and enforces a human accuracy verification gate
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# AI summary and verification

Generate plain-language customer summaries with an automated accuracy verification gate.

## Why a human accuracy gate

Large Language Models frequently invent convincing features, exaggerate performance numbers, or synthesize obsolete context. Publishing unverified generative summaries risks customer confusion and compliance breaches.

DocsCI treats every AI output as an unverified proposal. The tool splits generated summaries into atomic claims, verifies each claim against Git commit evidence, and blocks automated publication until a technical writer reviews the draft.

## Generating verified summaries

To generate an AI release draft:

```bash
export GEMINI_API_KEY="your-api-key"
docsci release-notes --from v1.0.0 --to v1.1.0 --ai-summary
```

If you omit `GEMINI_API_KEY`, DocsCI runs offline using an integrated mock client.

## Verification algorithm

The verification engine performs these steps:

1. Split summary prose into atomic claims.
2. Extract key content nouns and technical scopes.
3. Compare claims against commit descriptions, scopes, and breaking changes.
4. Mark statements as `SUPPORTED` or `UNSUPPORTED`.
5. Emit `RELEASE_NOTES_DRAFT.md` containing an audit table and a review warning banner.

## Failure modes and limitations

Be aware of these generative limitations:

- **Hallucination**: The model may describe features absent from the commits.
- **Scope inflation**: The model may exaggerate minor bug fixes into major architectural updates.
- **Stale context**: The model may assume legacy behaviors from training weights rather than repository reality.

Review [documented failure modes](failure-modes.md) for real-world examples caught by the verifier.
