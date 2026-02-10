FROM python:3.13-slim

# Install system dependencies (curl + poppler)
RUN apt-get update && \
    apt-get install -y curl poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency file first (better caching)
COPY pyproject.toml .

# Install Python deps
RUN uv export --group data-collection --no-hashes > requirements.txt
RUN uv pip install --system -r requirements.txt

# Copy source code
COPY helper /app/helper
COPY data_collection /app/data_collection

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

CMD ["python"]
