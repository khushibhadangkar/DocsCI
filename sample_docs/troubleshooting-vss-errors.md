---
title: Troubleshooting VSS errors
description: Resolving Volume Shadow Copy Service errors on Windows Server
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Troubleshooting Windows VSS snapshot errors

Microsoft Volume Shadow Copy Service creates crash-consistent disk states.

## Resolving VSS writer timeouts

When VSS writers enter an unstable state, the operating system rejects new snapshot requests.
Restart the Volume Shadow Copy service to reset unresponsive system writers.

Follow this procedure:

1. Open PowerShell with Administrator privileges.
2. Run `vssadmin list writers` to identify failed writer components.
3. Restart the Cryptographic and VSS system services.
