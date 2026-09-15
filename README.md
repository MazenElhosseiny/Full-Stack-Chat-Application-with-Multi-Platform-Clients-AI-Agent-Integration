# AI Agent Harness

A Claude Code–style AI agent built from scratch in Python. It accepts prompts over HTTP, calls a local LLM through [Ollama](https://ollama.com) using the `openai` Python library, and executes tool calls (file I/O, shell commands) in a sandboxed container — including a self-modifying mode where the agent can extend its own toolset at runtime.

## What it does

1. Receives a prompt via `POST /chat`
2. Sends the prompt + tool schemas to a local LLM (`llama3.2:3b`) using native tool calling
3. If the model requests a tool call, executes it and feeds the result back to the model
4. Repeats until the model returns a final answer (or hits a max-iteration safety limit)
5. Returns the final response as JSON

This is the same fundamental architecture behind tools like Claude Code and GitHub Copilot's agent modes: a **prompt → execute → feedback loop**, driven by the model's own decisions about when and how to use tools.

## Tools implemented

| Tool | Description |
|---|---|
| `read_file(path)` | Reads and returns the contents of a file |
| `write_file(path, content)` | Writes content to a file, creating parent directories as needed |
| `run_command(command)` | Executes a shell command and returns stdout/stderr |

Each tool always returns a string — including on failure — so the model can see and reason about errors rather than the process crashing.

## Architecture

```
Client → HTTP POST /chat → Agent Harness
                               │
                          Ollama (llama3.2:3b)
                          Tool execution (sandboxed)
```

- **`harness.py`** — the agent loop, tool implementations, and HTTP server
- **`Containerfile`** — installs Ollama + Python deps, runs the harness in an isolated container
- Model responses are parsed for `tool_calls`; each call is dispatched to its Python implementation via a simple name → function registry

## Running it

**Stage 1 (bare process):**
```bash
pip install openai requests
python harness.py
curl -X POST http://localhost:9090/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "read the file /etc/hostname and tell me what it says"}'
```

**Stage 2 (sandboxed):**
```bash
podman build -t agent-harness .
podman run -p 9090:9090 -v ollama-models:/root/.ollama agent-harness
```

**Stage 3 (self-modifying):**
```bash
podman run -p 9090:9090 \
  -v ollama-models:/root/.ollama \
  -v "$(pwd):/app" agent-harness
# Try: "add a tool called http_get that fetches a URL"
```

## Why sandboxing matters

An LLM-driven agent with shell access is fundamentally unpredictable — there's no reliable way to guarantee it will only ever do sensible, intended things. Stage 1 makes this concrete: without isolation, safety depends entirely on careful prompting, with nothing technical backing it up. Stage 2 replaces that with a real, structural guarantee — Linux namespaces mean a command can execute exactly as given and still do zero damage to the host, because its entire filesystem view is a walled-off container image, not the real machine.

## Tech stack

Python · Ollama · `llama3.2:3b` · OpenAI Python library (as an OpenAI-compatible client) · Podman · native LLM tool calling

## Notes on production use

Running local inference (Ollama) is ideal for development — free, offline, fully inspectable. A production deployment would swap in a hosted model provider (any OpenAI-compatible API) via environment variables alone, with no code changes required. Self-modification in production would also need real safeguards this learning version doesn't have: diff review before restart, sandboxed validation of new code, and checkpointing before any self-modifying run.


Demo:


https://github.com/user-attachments/assets/c155e7b2-4563-4b65-a978-e25399267d30
