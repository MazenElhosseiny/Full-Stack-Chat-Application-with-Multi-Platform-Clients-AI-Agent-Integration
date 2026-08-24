# Ollama Setup Guide

Ollama runs LLMs locally on your machine — no API keys, no network calls, no cost.

## Installation

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS
Download from [ollama.com](https://ollama.com) or use Homebrew:
```bash
brew install ollama
```

### Windows
Download from [ollama.com](https://ollama.com)

## Verify Installation

```bash
ollama --version
```

## Pull a Model

For this project, use `llama3.2:3b` — it supports native tool calling, which is
required for the agent harness. Smaller models like `gemma:2b` do NOT reliably
support tool calling.

```bash
# llama3.2 3B — ~2GB, runs on CPU, supports tool calling ✅
ollama pull llama3.2:3b

# Do NOT use gemma:2b — it does not reliably support tool calling ❌
```

## Test the Model

```bash
ollama run llama3.2:3b "What is HTTP?"
```

You should see a response stream in your terminal. Press Ctrl+D to exit.

## Start the API Server

The harness communicates with Ollama via its HTTP API (default: `http://localhost:11434`):

```bash
# Start Ollama's API server (usually runs automatically after install)
ollama serve
```

## Test the API Directly

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2:3b",
  "messages": [{"role": "user", "content": "Say hello in exactly 3 words."}],
  "stream": false
}'
```

## Test Tool Calling

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2:3b",
  "messages": [{"role": "user", "content": "What time is it?"}],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_time",
        "description": "Get the current time",
        "parameters": {"type": "object", "properties": {}}
      }
    }
  ],
  "stream": false
}'
```

If tool calling is working, the response will contain a `tool_calls` array
instead of plain text content.

## Using the openai Python Library

The harness uses the `openai` Python library pointed at Ollama's OpenAI-compatible
endpoint. Install it with:

```bash
pip install openai
```

The library connects to Ollama at `http://localhost:11434/v1` — the same API
interface as OpenAI, just running locally.

## Container Networking

If Ollama runs on your host and the harness runs in a container:

```python
# Use host.containers.internal to reach the host from inside a container
client = OpenAI(
    base_url="http://host.containers.internal:11434/v1",
    api_key="ollama"
)
```

Or set the environment variable:
```bash
export OLLAMA_URL=http://host.containers.internal:11434
```

If Ollama runs inside the harness container (as in the Containerfile):
```python
# Use localhost — Ollama is in the same container
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
```

## Troubleshooting

| Problem | Solution |
|---|---|
| `ollama: command not found` | Re-run the install script or check your PATH |
| `connection refused` on port 11434 | Run `ollama serve` in another terminal |
| Model pull is slow | llama3.2:3b is ~2GB — be patient on slow connections |
| Tool calls not working | Make sure you're using `llama3.2:3b`, not `gemma:2b` |
| Out of memory | Close other applications. llama3.2:3b needs ~2GB RAM |
| Container can't reach Ollama | If Ollama runs on the host, use `host.containers.internal:11434` or `--network host` |
| `ModuleNotFoundError: openai` | Run `pip install openai` |