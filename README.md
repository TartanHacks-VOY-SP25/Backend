# Development Environment Setup for Backend Repository
This repository contains the backend service for the PostMarq Hackathon submission
This document contains the details on how to bring this service up and online.

## Required Components/Toolchains
- Docker, Docker runtime (colima on macos works also)
- Visual Studio Code, Visual Studio Code Devcontainers extension
- postgres:15 Docker image pulled

## Environment Setup Steps
1. Ensure that docker, docker runtimes are working properly
2. Launch Vscode, and clone this repository into a directory. 
Open the repository in vscode, and us ctrl/cmd + shift + p to launch this repository in a container defined by the devcontainer.json and Dockerfile
This may take some time
3. In an external terminal, run the following command:
`docker run --name backend-postgres -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=mydatabase -p 5432:5432 -d postgres:15`
4. In the same external terminal, run the following command:
`docker exec -it backend-postgres bash`
5. From within the container shell (that you just opened), run the following command:
`psql -U myuser -d mydatabase`
6. Copy the entire contents of the `./database/database.psql` file into the psql shell that you just opened, and hit enter. 
This will setup the development postgres db.
7. From within your Vscode instance, open the integrated terminal.
8. Run `fastapi run` (or `fastapi dev` if you need hot reload). This will start the backend fastapi service.
9. You can now view the api docs at `localhost:8000/docs`.
10. Next steps are now to start the frontend service and use the application. Instructions for bringing up the frontend service are in the frontend repository.



