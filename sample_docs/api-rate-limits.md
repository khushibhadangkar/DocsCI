---
title: API rate limits
description: REST API request throttling, headers, and retry strategies
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# REST API rate limits and throttling

CloudVault enforces request rate limits to guarantee system stability and prevent denial-of-service degradation.

## Rate limit thresholds

The gateway restricts clients to 1,000 requests per minute per access token.
When client applications exceed rate limits, the gateway returns HTTP 429 Too Many Requests responses.
Client integrations should implement exponential backoff retry algorithms.

Review [role-based access control](rbac-access-control.md) for permission details.
