# Use a real OS + Python
FROM python:3.13-slim

# Install curl (needed to install uv)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency file first (better layer caching)
COPY pyproject.toml .

# Export and install deps
RUN uv export --only-group data-collection --no-hashes > requirements.txt
RUN uv pip install --system -r requirements.txt

# Copy source code
COPY helper /app/helper
COPY data_collection /app/data_collection

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

CMD ["python"]
