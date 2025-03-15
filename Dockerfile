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
    gcc \
    libpq-dev \
    sqlite3 \
    libsqlite3-dev \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy local code to the container image.
COPY . .

# Install project dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt


# Run the web service on container startup.
CMD ["hypercorn", "main:app", "--bind", "::"]
