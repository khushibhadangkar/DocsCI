---
title: Understanding recovery points
description: RPO calculations and snapshot granularity
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Understanding recovery points and recovery objectives

Recovery points define the state of application data at a specific moment in time.

## Recovery point objectives

A recovery point objective establishes the maximum acceptable data loss interval during unplanned downtime.
The agent captures snapshot records every fifteen minutes for mission-critical databases.
Shorter intervals minimize potential data loss during unexpected failover scenarios.
