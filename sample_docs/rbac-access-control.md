---
title: RBAC access control
description: Role-based access control policies for backup administrators and operators
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Role-Based Access Control Overview

Granular permissions prevent unauthorized backup deletion or encryption key export.

## Role definitions

Three built-in roles govern platform capabilities: Backup Admin, Operator, and Auditor.
An auth token is required for every programmatic API invocation.
Permissions are evaluated by the authorization layer before executing sensitive storage actions.

1. Select Users and Roles from the administration console.
2. Assign appropriate privilege tiers to the team member.
3. Confirm the role assignment.
