# AI Chatbot

This project is a Flask chatbot UI that talks to a local Ollama model and can run either directly or in Docker.

## Local Run

Install dependencies:

```powershell
pip install -r requirements.txt
```

Make sure Ollama is installed and a model is available:

```powershell
ollama pull llama3.2
```

Run the app:

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.

## Docker Run

Build and start with Docker Compose:

```powershell
docker compose up --build
```

Open `http://127.0.0.1:5000`.

## Jenkins Integration

This repo includes a `Jenkinsfile` for a simple CI pipeline on a Windows Jenkins agent and is ready to be used from a GitHub repository.

What the pipeline does:

1. Checks out the repository
2. Builds the Docker image
3. Runs the container with the local `.env`
4. Verifies the app using `http://127.0.0.1:5000/health`
5. Prints container logs and removes the container

Jenkins agent requirements:

- Git
- Docker Desktop or Docker Engine with CLI access
- PowerShell

Recommended Jenkins job type:

- Pipeline job
- Pipeline script from SCM
- SCM: Git
- Repository source: GitHub

If Jenkins runs on the same machine as Ollama, the default pipeline works as-is because the container points to `http://host.docker.internal:11434`.

If Jenkins runs on another machine, update `.env` or the `docker run` command in `Jenkinsfile` so `OLLAMA_HOST` points to the reachable Ollama server.

## GitHub With Jenkins

Use GitHub as the source repository for the Jenkins pipeline:

1. Push this project to a GitHub repository.
2. In Jenkins, create a new Pipeline job.
3. Choose `Pipeline script from SCM`.
4. Select `Git`.
5. Paste your GitHub repository URL.
6. If the repo is private, add Jenkins credentials for GitHub and select them in the job.
7. Set the script path to `Jenkinsfile`.

To trigger Jenkins automatically from GitHub:

1. Install or enable the GitHub integration plugins in Jenkins.
2. In the Jenkins job, enable `GitHub hook trigger for GITScm polling` if your Jenkins UI shows that option.
3. In GitHub, open your repository settings and add a webhook.
4. Use this webhook URL:

```text
http://your-jenkins-url/github-webhook/
```

5. Content type should be `application/json`.
6. Select the `Just the push event` trigger.

After that, a push to GitHub can trigger the Jenkins pipeline automatically.

If your Jenkins server is not publicly reachable, you can still use:

- manual builds from Jenkins
- polling from Jenkins
- GitHub through a VPN, reverse proxy, or tunneling setup

## Private Repos

For private GitHub repositories, the usual Jenkins setup is:

- add a GitHub Personal Access Token in Jenkins Credentials
- use that credential in the Pipeline job SCM section
- keep `.env` on the Jenkins machine if you do not want to commit it to GitHub

Do not commit secrets to GitHub. Keep values like `FLASK_SECRET_KEY` and environment-specific configuration in Jenkins credentials, Jenkins environment variables, or a local `.env` file on the Jenkins agent.
