# Maintenance and Preflight Checks

The Muse Edit project uses automated preflight checks before merge and deployment.

The preflight script is located at:

scripts/preflight.py

It verifies:

- required project files;
- Python compilation;
- FastAPI application import;
- React production build;
- Dockerfile configuration for Render;
- .env protection through .gitignore;
- .env.example safety and placeholder values.

The preflight can be executed locally with:

python3 scripts/preflight.py

A successful run should finish with:

Passed 11/11 checks
Preflight passed.

GitHub Actions runs the same preflight checks automatically for pull requests to main and for pushes to main.

The CI workflow is located at:

.github/workflows/preflight.yml

The CI workflow was tested using an intentional failure. The first workflow run failed as expected. The intentional failure was then removed, and the following workflow run passed successfully.

Secrets must never be committed to Git. The local .env file is ignored, while .env.example contains only placeholder values.

Production is deployed through Render.

Production domain:

https://themuse.space

Swagger:

https://themuse.space/docs

After changes are merged into main, the production deployment should be checked and a smoke test should confirm that the application is available.