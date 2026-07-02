# Stage 1: Build dependencies
FROM python:3.12-slim as builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --user --no-cache-dir .

# Stage 2: Runtime
FROM python:3.12-alpine
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY poe_tablet_tool ./poe_tablet_tool
COPY static ./static

# Ensure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Set Python buffer size for better performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["poe-tablet-api"]
