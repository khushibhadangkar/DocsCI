---
title: Disaster recovery failover runbook
description: Automated failover and site recovery procedures
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Disaster Recovery Failover Procedures

Execute rapid switchover to standby cloud compute instances during major datacenter outages.

## Triggering failover

In a disaster scenario, fail-over is executed by the site recovery coordinator.
All production traffic is redirected by global DNS balancers to secondary target regions.

Follow these steps:
1. Navigating to the Disaster Recovery dashboard is necessary.
2. Select the secondary recovery region.
3. Click Initiate Failover.
