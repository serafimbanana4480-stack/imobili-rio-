# Terraform Infrastructure (WIP)

This directory contains a **work-in-progress** Terraform configuration for the Real Estate Opportunity Engine.

## Status

Currently a stub. The existing `main.tf` only copies local files and does **not** provision any real cloud infrastructure (VPC, ECS/Cloud Run, RDS, ElastiCache, S3, etc.).

## Roadmap

- [ ] AWS/GCP/Azure provider configuration
- [ ] VPC / networking
- [ ] Container runtime (ECS Fargate or Cloud Run)
- [ ] Managed database (RDS PostgreSQL or Cloud SQL)
- [ ] Managed cache (ElastiCache Redis or Memorystore)
- [ ] Object storage (S3 or GCS) for backups & exports
- [ ] CI/CD pipeline integration

## Usage

Do **not** use this for production deployments until the roadmap items above are implemented.

For local development, use `docker-compose.yml` at the repository root instead.
