# Week 8 — AI Agent Harness

## Overview

Build a Claude Code-like AI agent harness. It accepts prompts via HTTP, calls
a local LLM through Ollama using the `openai` Python library, executes tool
calls in a sandboxed container, and can even modify its own source code.

Your Week 5 full-stack application (Flask API, SQLite persistence, JWT auth,
chat frontend) now talks to an AI — the "echo" has become an LLM.

## Architecture

```
Browser → nginx → API server → Agent Harness container
                                   │
                              Ollama (llama3.2:3b)
                              Tool execution (inside same container)
```

The Agent Harness container **is** the sandbox. Tool calls execute inside it.
The container boundary protects your host machine.

## Starting Point

Your Week 5 full-stack application. The API server will forward `POST /chat`
to the Agent Harness instead of echoing or querying the database.

## Learning Objectives

- Understand the tool-use architecture behind AI coding agents
- Implement a prompt → execute → feedback loop
- Use Ollama to run LLMs locally with native tool calling
- Experience why sandboxing is essential for code-executing agents
- Build a system that can modify its own behavior

## What You're Given

| File | Description |
|---|---|
| `harness.py` | Agent harness skeleton — the main loop (TODO), tool definitions (TODO), HTTP endpoint (given), tool schemas (given), LLM client (given) |
| `Containerfile` | Container definition with Ollama and Python |
| `ollama-setup.md` | Guide for installing Ollama and pulling models |
| `lab-report.md` | Template for your sandboxing and AI safety analysis |

### What's Given vs. What You Build

**Given (do not modify):**
- `openai` client setup (pointed at Ollama)
- Tool schemas (JSON schemas for `read_file`, `write_file`, `run_command`)
- HTTP server boilerplate (`HarnessHandler`, `main()`)
- `SYSTEM_PROMPT`
- `call_llm()` — the LLM client wrapper

**You build (TODOs):**
- `tool_read_file(path)` — read and return file contents
- `tool_write_file(path, content)` — write content to a file
- `tool_run_command(command)` — execute a shell command
- `run_agent(user_message)` — the agent loop

### File Map — where each slide lives in harness.py

| Section of harness.py (top → bottom) | Taught on slide | Who builds it |
|---|---|---|
| Config (`OLLAMA_URL`, `MODEL`, `MODEL_API_KEY`) | Ollama Setup (Part 5) + Sprites deploy | Given |
| `client = OpenAI(...)` | The Shape of the Conversation | Given |
| `SYSTEM_PROMPT` | The `system` role | Given |
| `TOOLS` — JSON schemas | Step 5a | Given — do not modify |
| `tool_read_file` / `tool_write_file` / `tool_run_command` | Step 3 (executing model output) | **You** |
| `TOOL_IMPLS` registry | Step 6b lookup | Given |
| `call_llm()` | Step 1 | Given |
| `run_agent()` — the loop | Steps 6a–6b | **You** |
| Self-reload (`os.execv`) | Stage 3 | Given |
| `HarnessHandler.do_POST` | Step 4 | Given |
| `main()` / `ThreadingHTTPServer` | Step 4 | Given |

The slides build this file conceptually (call → code → execute → endpoint →
tools → loop → context); the file is assembled top-to-bottom. The two TODO
blocks are where your work goes — everything else exists to make them work.

## What You Need to Build

### 1. The Agent Loop

```
1. Receive prompt from API (POST /chat)
2. Send prompt + tool schemas to LLM via openai library
3. Check LLM response for tool_calls
4. If tool calls found:
   a. Execute them (look up in TOOL_IMPLS)
   b. Feed results back to the LLM as tool messages
   c. Go to step 2
5. If no tool calls: return the response as the final answer
6. Stop after MAX_ITERATIONS (10) to prevent infinite loops
```

### 2. Tool Implementations

| Tool | What it does |
|---|---|
| `read_file(path)` | Read and return file contents |
| `write_file(path, content)` | Write content to a file |
| `run_command(cmd)` | Execute a shell command, return stdout/stderr |

### 3. Three Stages of Progression

**Stage 1 — Bare process.** Run `harness.py` directly on your host. Ask it to
read and write files. It works — but notice it has access to your entire
filesystem. Ask it to delete a test file. It succeeds. Nothing stopped it.

**Stage 2 — Sandboxed.** Build the container and run the harness inside it.
Ask it to `rm -rf /`. Watch it destroy the container's filesystem — but your
host is untouched. Remove the container and run a fresh one from the image —
everything is back. **This is why sandboxing exists.**

**Stage 3 — Self-modifying.** Mount the harness source code into the container.
Ask the agent: "add a new tool called `http_get` that can fetch a URL and return
the response." The agent writes the code, the harness detects its source changed
and restarts itself, and the new tool works. You've built something that can
build itself.

### 4. API Integration

Update your Week 5 Flask API server (`server.py`). In the `/chat` route,
forward the message to the harness, then persist the exchange in SQLite
just like Week 5 did:

```python
# In server.py — replace the placeholder in the /chat route:
import requests  # add 'requests' to requirements.txt!

HARNESS_URL = os.getenv('HARNESS_URL', 'http://harness:9090')

@app.route('/chat', methods=['POST'])
def chat():
    body = request.get_json(silent=True) or {}
    message = body.get('message')
    if not message:
        return jsonify({'error': 'message required'}), 400

    # Forward to the agent harness. Use a long timeout — an agent loop
    # on a 3B CPU model can take minutes.
    resp = requests.post(
        f'{HARNESS_URL}/chat',
        json={'message': message},
        timeout=300,
    )
    ai_response = resp.json()['response']

    # Keep Week 5 behavior: persist the exchange in SQLite
    db = get_db()
    db.execute(
        'INSERT INTO messages (message, response) VALUES (?, ?)',
        (message, ai_response),
    )
    db.commit()

    return jsonify({'response': ai_response}), 201
```

The harness has **no authentication** — JWT auth already guards `/chat` at
the API layer, so the harness must only be reachable from the API container.
In `compose.yml`, use `expose` (internal network only), never `ports`
(which would publish it on your host unauthenticated).

**Timeouts — this will bite you:** agent loops are slow. You must raise
timeouts at every hop:

- `requests.post(..., timeout=300)` (above)
- gunicorn in `api/Containerfile`: add `--timeout 300` to the CMD — the
  default 30s kills the worker mid-request
- nginx `location /chat` block: add `proxy_read_timeout 300s;` — the
  default 60s returns a 504 while the agent is still thinking

Add the harness to your `compose.yml`:
```yaml
  harness:
    build: ./harness
    expose:
      - "9090"
    # Ollama runs inside the harness container by default (see Containerfile).
    # To use Ollama running on your host instead, uncomment:
    # environment:
    #   - OLLAMA_URL=http://host.containers.internal:11434
    volumes:
      - ollama-models:/root/.ollama    # cache the model (~2GB) across recreations
      # - ./harness:/app               # Stage 3 only: self-modification

volumes:
  ollama-models:
```

This assumes you copy the `week8-agent-harness` files into a `harness/`
subdirectory of your Week 5 project. Standalone (testing this directory by
itself), use `-v "$(pwd):/app"` instead.

### Ollama Networking

If Ollama runs on your host (recommended for development):
```python
client = OpenAI(
    base_url="http://host.containers.internal:11434/v1",
    api_key="ollama"
)
```

If Ollama runs inside the harness container (as in the Containerfile):
```python
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
```

The Containerfile already installs `zstd` alongside `curl` — the Ollama
installer switched to zstd-compressed packages and aborts mid-build
(`This version requires zstd for extraction`) without it. If you rewrote
the Containerfile, keep both packages in the `apt-get install` line.

## Testing

```bash
# Install dependencies
pip install openai requests

# Stage 1: Run directly
python harness.py
curl -X POST http://localhost:9090/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "read the file /etc/hostname and tell me what it says"}'

# Stage 2: Run in container
podman build -t agent-harness .
# Cache the model so recreating the container doesn't re-download 2GB:
podman run -p 9090:9090 -v ollama-models:/root/.ollama agent-harness
# Try: "delete everything in /" — watch it fail safely

# Stage 3: Self-modification (run from this directory)
podman run -p 9090:9090 \
  -v ollama-models:/root/.ollama \
  -v "$(pwd):/app" agent-harness
# Try: "add a tool called http_get that fetches a URL"
# The agent rewrites harness.py; the harness detects the change and
# restarts itself with the new code.
```

## Deliverables

1. Working `harness.py` with all three tools and the agent loop implemented
2. `Containerfile` for the sandboxed harness
3. Updated `compose.yml` with the harness service
4. Updated API server that forwards to the harness
5. Completed `lab-report.md`
6. Push to your GitLab repository

## Tips

- Start with a simple prompt → response loop (no tools) and verify Ollama works
- Add one tool at a time — `read_file` first, then `write_file`, then `run_command`
- Use `json.loads()` to parse `tool_call.function.arguments` into a dict
- Use `subprocess.run()` with `timeout=30` for shell commands
- The self-modification stage is the hardest — get Stages 1 and 2 working first
- Make sure you're using `llama3.2:3b` — it supports native tool calling

## Deploying Later? (Sprites, etc.)

If you eventually host the full-stack app on a [sprite.dev](https://sprites.dev)
sprite or another cloud VM, **use a cloud model provider in production** — don't
run local Ollama there. Sprites sleep after ~30 seconds idle and only bill while
awake; local inference keeps the sprite active at full CPU for every response,
defeating the pricing model. The switch is just environment variables:

```bash
# Production env vars — code unchanged
OLLAMA_URL=https://openrouter.ai/api   # or any OpenAI-compatible provider
MODEL_API_KEY=sk-...                   # never commit this; set it on the sprite
MODEL=meta-llama/llama-3.3-70b-instruct
```

The harness already reads all three: `OLLAMA_URL`, `MODEL_API_KEY`, and `MODEL`
(with `llama3.2:3b` as the local default). On startup it prints which mode it's
in — check that line before assuming it's talking to the right endpoint.

Keep Ollama on your laptop for development (free, offline, every request
visible); let the hosted model serve production (fast, cheap, better tool
calling than a 3B model). Bonus: sprite checkpoints give you Stage 2's "remove
and recreate" safety as a production feature — checkpoint before letting your
self-modifying agent run, restore if it wrecks itself. Also remember the Week 5
rules: JWT auth stays enforced, and the harness port is never exposed publicly.