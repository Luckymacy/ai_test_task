# AGENTS.md

This repository contains the Dress Rental Planner / The Muse Edit project.

Main components:
- FastAPI backend in app/
- React admin interface in admin/
- PostgreSQL database hosted in Neon
- OpenAI integration for AI analysis and assistant features
- Docker deployment to Render

Development rules:

1. Never commit secrets.
2. The .env file must stay excluded from Git.
3. Use .env.example only with placeholder values.
4. Before creating a commit, run the project preflight checks.
5. Backend changes must keep the FastAPI application importable.
6. Frontend changes must pass the React/Vite build.
7. Docker configuration must remain valid for Render deployment.
8. AI write actions must remain controlled and require user confirmation.
9. Read-only AI tools must not modify database data.
10. Keep documentation updated when deployment or maintenance behavior changes.

Preflight checks should verify:
- Python files compile successfully.
- Required backend modules import successfully.
- React production build succeeds.
- Dockerfile exists and contains the expected FastAPI/Uvicorn startup command.
- .env is ignored by Git.
- .env.example does not contain real secrets.
- Required project files are present.

Production:
- Render deployment uses Docker.
- Custom domain: https://themuse.space
- Swagger: https://themuse.space/docs