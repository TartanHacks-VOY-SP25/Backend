
# Use the Python 3 alpine official image
# https://hub.docker.com/_/python
FROM python:3-alpine

# Create and change to the app directory
WORKDIR /app

# Install development dependencies
RUN apk add --no-cache \
    git \
    bash \
    curl \
    openssh \
    gcc \
    musl-dev \
    postgresql-dev \
    sqlite \
    sqlite-dev


# Copy local code to the container image.
COPY . .

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup.
CMD ["hypercorn", "main:app", "--bind", "::"]
