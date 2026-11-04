---
title: API rate limits
description: REST API request throttling, headers, and retry strategies
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# REST API Rate Limits and Throttling

CloudVault enforces request rate limits to guarantee system stability and prevent denial-of-service degradation.

## Rate limit thresholds

Clients are restricted to 1,000 requests per minute per security token.
HTTP 429 Too Many Requests responses are returned by the gateway when rate limits are exceeded.
Obviously, client integrations should implement exponential backoff algorithms.

Review the [invalid link](invalid-spec-url.md) for endpoint limits.
