---
title: Troubleshooting failed backups
description: Diagnose and resolve common backup job execution errors
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Troubleshooting Failed Backup Routines

When a backup task fails, examine system event logs to identify root causes.

## Common error codes

Backups are interrupted by socket timeouts whenever network throughput falls below threshold.
Clearly, intermittent network congestion causes transient connection drops.

Check the following items:
1. Verifying network firewall configurations should be done first.
2. Ensure port 9443 is open across all intermediate routers.
3. Review the CloudVault agent service status.
