## Migrations Folder

This directory contains **one-off migration scripts** used to evolve the PostgreSQL schema and data over time.

- `schema/` – core schema and feature migrations that create or alter database tables and columns (e.g. agreements, templates, StudySite, feasibility, chat, access control).
- `feature/` – reserved for higher-level, feature-specific migrations that orchestrate multiple schema changes or data moves (currently unused, but kept for future organization).
- `archive/` – historical or experimental migration scripts that have been superseded by the scripts in `schema/`. These are kept for audit purposes only and should not be run in new environments.

**Important:**
- These scripts are not imported by the FastAPI app and are intended to be run manually (or via ops tooling) when needed.
- Do **not** delete or rewrite them without confirming with the migration history and production rollout plan.

