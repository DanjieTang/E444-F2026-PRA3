FROM python:3.10-slim

# Install uv to install dependencies from uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first so this layer is cached when only app code changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the app and its templates
COPY activity1-4.py ./
COPY templates ./templates

# Use the virtualenv that uv created
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

# Bind to 0.0.0.0 so the server is reachable from outside the container
CMD ["flask", "--app", "activity1-4.py", "run", "--host=0.0.0.0", "--port=5000"]
