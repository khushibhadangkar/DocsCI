---
title: Manage audit logs
description: Security log retention, export, and compliance verification
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Managing Audit Logs and Security Records

CloudVault maintains tamper-evident audit trails for every administrative operation.

## Log streaming

Audit records are transmitted by the security daemon to designated SIEM collectors.
Basically, administrators can export JSON logs directly into Splunk or Datadog.

1. Locate the Security and Audit section in settings.
2. The user must provide the remote syslog endpoint address.
3. Save the forwarding settings.
