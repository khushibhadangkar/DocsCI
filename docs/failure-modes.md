---
title: Failure modes in AI release summaries
description: Documented cases where AI summarization hallucinated and how the verifier caught it
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Failure modes in AI release summaries

Study real-world generative failure modes, verifier detection mechanisms, and prompt improvements.

## Overview

Generative AI models can produce fluent, plausible statements that are technically false. DocsCI pairs prompt engineering with a deterministic verification gate to catch inaccuracies before human review.

## Case 1: Invented post-quantum encryption

- **Commit input**: `feat(vault): add AES-256 GCM encryption for archive chunks (#44)`
- **AI-generated claim**: "Introduced post-quantum hybrid lattice cryptography across all enterprise repositories."
- **How DocsCI caught it**: The verifier found zero occurrences of "quantum", "hybrid", or "lattice" in the commit index and marked the statement `UNSUPPORTED`.
- **Prompt change**: Added constraint: *"Do not extrapolate cryptographic algorithms or security tiers beyond specific primitives cited in commit messages."*

## Case 2: Exaggerated throughput metrics

- **Commit input**: `perf(network): optimize buffer recycling in socket stream (#48)`
- **AI-generated claim**: "Accelerated cross-region snapshot replication throughput by 10x with zero CPU overhead."
- **How DocsCI caught it**: The claim asserted quantitative multipliers (`10x`) and zero-overhead claims unsupported by commit text, triggering an `UNSUPPORTED` flag.
- **Prompt change**: Added constraint: *"Never invent percentages, multipliers, or numerical performance metrics unless explicitly given in the input commits."*

## Case 3: False cloud platform support

- **Commit input**: `feat(s3): add support for AWS S3 Object Lock retention (#52)`
- **AI-generated claim**: "Expanded immutable storage across AWS S3, Google Cloud Storage, and Azure Blob."
- **How DocsCI caught it**: The verifier detected that Google Cloud Storage and Azure Blob were absent from the commit range, failing the claim.
- **Prompt change**: Added constraint: *"Restrict cloud provider mentions strictly to the specific cloud platforms modified in the commits."*

## Case 4: Fabricated backward compatibility guarantee

- **Commit input**: `feat(auth)!: remove legacy v1 token endpoint (#60)`
- **AI-generated claim**: "Maintains full backward compatibility for all legacy v1 authentication workflows."
- **How DocsCI caught it**: The commit carried an explicit breaking change marker (`!`), directly contradicting the claim. The verifier flagged the statement as `UNSUPPORTED`.
- **Prompt change**: Added constraint: *"Check for breaking change indicators and state breaking impacts directly instead of claiming compatibility."*

## Case 5: Invented disaster recovery SLA guarantees

- **Commit input**: `fix(failover): resolve DNS timeout during manual failover trigger (#65)`
- **AI-generated claim**: "Guarantees automated five-minute disaster recovery SLA with zero manual intervention."
- **How DocsCI caught it**: The commit described manual failover DNS timeout resolution rather than automated SLA guarantees. The verifier marked the claim `UNSUPPORTED`.
- **Prompt change**: Added constraint: *"Never assert legal warranties, automated SLAs, or compliance guarantees without explicit commit confirmation."*
