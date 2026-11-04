---
title: Concept of retention policies
description: Overview of snapshot lifecycles and retention rules
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Concept: retention policies and rules

Retention rules govern how long backup archives persist in designated repositories.

## Overview of retention

Snapshots persist across daily, weekly, and monthly intervals.

The policy scheduler triggers a backup job when expiration timestamps arrive.
Automated pruning routines remove obsolete archives according to policy settings.
See the [overview section](#overview-of-retention) for general lifecycle details.
