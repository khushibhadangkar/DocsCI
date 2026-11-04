---
title: Troubleshooting failed backups
description: Diagnose and resolve common backup job execution errors
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Troubleshooting failed backup jobs

When a backup job fails, examine system event logs to identify root causes.

## Common error codes

Network timeouts interrupt backups whenever data transfer rates drop below configured minimums.
Intermittent network congestion causes transient connection drops.

Check the following items:

1. Verify network firewall rules.
2. Ensure port 9443 is open across intermediate routers.
3. Review the CloudVault agent service status.
