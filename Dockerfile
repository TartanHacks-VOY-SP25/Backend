# https://hub.docker.com/_/python
FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive

# Create and change to the app directory
WORKDIR /app

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    bash \
    openssh-client \
    make \
    gcc \
    libpq-dev \
    sqlite3 \
    libsqlite3-dev \
    python3 \
    python3-pip \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy local code to the container image.
COPY . .

# Install project dependencies
RUN python3 -m pip install -r requirements.txt


# Run the web service on container startup.
CMD ["hypercorn", "main:app", "--bind", "::"]
