---
title: Configure S3 repository
description: Attach Amazon Web Services S3 bucket as a primary backup repository
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Configure S3 Repository Target

CloudVault stores encrypted archive chunks in Amazon S3 standard and Glacier storage classes.

## Prerequisites

Ensure you have created an AWS IAM user with appropriate PutObject and GetObject permissions.

1. Selecting the S3 option from the storage menu is your first step.
2. Enter the S3 bucket name and region.
3. Simply paste your AWS access keys into the fields.

Write-once disk guarantees can be enforced on AWS S3 Object Lock buckets.
