FROM node:22-bookworm-slim AS sdk

# Install Python and pip
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI (needed by claude-agent-sdk runtime)
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

# Python venv to avoid PEP 668 lockout
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5178
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5178"]
