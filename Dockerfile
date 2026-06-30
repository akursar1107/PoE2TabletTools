FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY poe_tablet_tool ./poe_tablet_tool
COPY static ./static

RUN pip install --no-cache-dir .

CMD ["poe-tablet-tool"]
