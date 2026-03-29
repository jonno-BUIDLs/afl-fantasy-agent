FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system -e .

COPY afl_fantasy/ ./afl_fantasy/

# Install Playwright browsers (needed for cookie extraction, not for normal operation)
# Comment this out if not using Playwright
# RUN playwright install --with-deps chromium

CMD ["afl-agent", "schedule"]
