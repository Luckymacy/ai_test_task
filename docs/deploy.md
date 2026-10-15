# Render Deployment

The Dress Rental Planner API is deployed to Render as a Docker Web Service.

Production URL:
https://the-muse-edit-api-luckymacy-141026-2149.onrender.com

Swagger documentation:
https://the-muse-edit-api-luckymacy-141026-2149.onrender.com/docs

Deployment branch:
deploy/render

Runtime:
Docker

The service starts FastAPI with Uvicorn and listens on the port provided by Render through the PORT environment variable.

Required environment variables are configured directly in Render and are not stored in Git:

- DATABASE_URL
- OPENAI_API_KEY
- BOT_TOKEN

The .env file is excluded from Git through .gitignore.

Before deployment, the Docker image was tested locally with:

docker build -t muse-edit-api .

and:

docker run --env-file .env -p 8000:8000 muse-edit-api

The production deployment was verified successfully. Render reported the service as Live, Uvicorn started successfully, and the Swagger documentation opened through the public Render URL.

The root URL currently returns 404 because the application does not define a GET / endpoint. This does not affect the API endpoints or /docs.

Deployment workflow:

1. Make deployment changes in the deploy/render branch.
2. Push the branch to GitHub.
3. Render builds the Docker image from the repository.
4. Verify production logs and the public URL.
5. Create a Pull Request.
6. Merge the verified deployment configuration into main.

Secrets must never be committed to Git.