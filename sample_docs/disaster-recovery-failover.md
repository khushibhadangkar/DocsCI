---
title: Disaster recovery failover runbook
description: Automated failover and site recovery procedures
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Disaster recovery failover procedures

Execute rapid failover to standby cloud compute instances during major datacenter outages.

## Triggering failover

In a disaster scenario, the site recovery coordinator executes automated failover sequences.
Global DNS balancers redirect production traffic to secondary target regions.

Follow these steps:

1. Navigate to the Disaster Recovery dashboard.
2. Select the secondary recovery region.
3. Click Initiate Failover.
