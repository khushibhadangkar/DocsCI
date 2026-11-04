---
title: Configure S3 repository
description: Attach Amazon Web Services S3 bucket as a primary backup repository
product_version: '2.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Configure S3 repository target

CloudVault stores encrypted archive chunks in Amazon S3 standard and Glacier storage classes.

## Prerequisites

Ensure you have created an AWS IAM user with appropriate PutObject and GetObject permissions.

## Attachment procedure

Follow these steps to connect your repository:

1. Select the S3 option from the storage menu.
2. Enter the S3 bucket name and region.
3. Paste your AWS credentials into the configuration fields.

Configure immutable storage settings on AWS S3 Object Lock buckets.
