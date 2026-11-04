---
title: Concept of retention policies
description: Overview of snapshot lifecycles and retention rules
product_version: '2.0'
last_reviewed: '2020-01-01'
owner: docs-team
---

# Concept: Retention Policies and Rules

Retention rules govern how long backup archives persist in designated repositories.

## Overview of retention

Snapshots can be retained on daily, weekly, and monthly intervals.

A backup process is initiated by the policy scheduler when expiration timestamps are reached.
Obviously, obsolete data is removed by automated pruning routines.
See the [local anchor](#missing-retention-anchor) for specific configuration flags.
