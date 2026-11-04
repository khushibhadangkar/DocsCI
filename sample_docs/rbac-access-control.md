---
title: RBAC access control
description: Role-based access control policies for backup administrators and operators
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Role-based access control overview

Granular permissions prevent unauthorized backup deletion or encryption key export.

## Role definitions

Three built-in roles govern platform capabilities: Backup Admin, Operator, and Auditor.
Every programmatic API invocation requires a valid access token.
The authorization layer evaluates permissions before executing sensitive storage actions.

Follow these steps:

1. Select Users and Roles from the administration console.
2. Assign appropriate privilege tiers to the team member.
3. Confirm the role assignment.
