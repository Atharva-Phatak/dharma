FROM ghcr.io/astral-sh/uv:latest
# Set workdir
WORKDIR /app

# Copy pyproject.toml
COPY pyproject.toml /app/

# Copy only your source code
COPY helper /app/helper
COPY data_collection /app/data_collection

# Install project dependencies + data-collection group using uv
RUN uv export --only-group data-collection --no-hashes > requirements.txt
RUN uv pip install --system -r requirements.txt

# Set env variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Start shell by default
CMD ["/bin/bash"]