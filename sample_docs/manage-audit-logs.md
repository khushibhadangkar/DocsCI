---
title: Manage audit logs
description: Security log retention, export, and compliance verification
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Managing audit logs and security records

CloudVault maintains tamper-evident audit trails for every administrative operation.

## Log streaming

The security daemon transmits audit records to designated SIEM collectors.
Administrators can export structured JSON logs directly into Splunk or Datadog.

Follow these steps:

1. Locate the Security and Audit section in settings.
2. Enter the remote syslog endpoint address.
3. Save the forwarding settings.
