"""
CSC 6304 — Week 8: AI Agent Harness

A Claude Code-like agent that:
1. Receives prompts via HTTP
2. Calls an LLM (local Ollama by default; any OpenAI-compatible provider
   works by setting OLLAMA_URL / MODEL / MODEL_API_KEY)
3. Uses native tool calling — the model returns structured tool_calls
4. Executes tools (read_file, write_file, run_command)
5. Feeds results back to the LLM in an agent loop
6. Returns the final response

Three stages of progression:
  Stage 1: Run directly on host (see the danger)
  Stage 2: Run in a container (see the safety)
  Stage 3: Self-modifying (see the power)
"""

import json
import os
import subprocess
import sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from openai import OpenAI  # pip install openai

# --- Configuration (slides: "Ollama Setup", Part 5) ---
# Dev default: local Ollama. Production (e.g., a sprite.dev sprite): set
# OLLAMA_URL to an OpenAI-compatible provider, MODEL to its model name, and
# MODEL_API_KEY to your key. Code never changes.
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
MODEL = os.environ.get('MODEL', 'llama3.2:3b')
API_KEY = os.environ.get('MODEL_API_KEY', 'ollama')
HARNESS_PORT = int(os.environ.get('HARNESS_PORT', '9090'))
MAX_ITERATIONS = 10

# --- OpenAI Client (slides: "The Shape of the Conversation") ---
client = OpenAI(
    base_url=f"{OLLAMA_URL}/v1",
    api_key=API_KEY,  # 'ollama' is a placeholder — local Ollama ignores it
)

# --- System Prompt (the "system" role from the slides) ---
SYSTEM_PROMPT = """You are a coding agent running inside a sandboxed container.
You have access to tools for reading files, writing files, and running shell
commands. Use these tools to accomplish the user's task.

When you need information from the filesystem, use read_file.
When you need to create or modify files, use write_file.
When you need to run a command, use run_command.

Continue using tools until you have enough information to answer the user's
question or complete their task. When you are done, respond with your answer
as plain text — do not call any more tools.

Important:
- File paths are relative to the container root (/)
- Shell commands run with a 30-second timeout
- Be careful with write_file — it overwrites existing files
- You are running in a sandbox — you cannot harm the host machine"""


# --- Step 5a: Tool Schemas (GIVEN — do not modify) ---
# These describe the tools to the LLM. The model sees these schemas
# and decides when to call each tool based on the descriptions.

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the contents of a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file at the given path. Creates parent directories if needed. Overwrites existing files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command and return its stdout and stderr. Commands run with a 30-second timeout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute",
                    }
                },
                "required": ["command"],
            },
        },
    },
]


# --- Step 3 + project work: Tool Implementations (YOU BUILD) ---
# TODO: Implement these three tools

def tool_read_file(path: str) -> str:
    """Read and return the contents of a file.

    The contract: always return a string — file contents on success, an
    error message on failure. The model reads errors too.
    """
    # try:
    #     1. open path in text mode
    #     2. read it, return the contents
    # except FileNotFoundError:
    #     3. return an error that names the path
    # except PermissionError:
    #     4. return an error that names the path
    # except IsADirectoryError:
    #     5. return an error that names the path
    # except UnicodeDecodeError:
    #     6. return an error that names the path
    pass


def tool_write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed.

    The contract: always return a string — a confirmation with a byte count
    on success, an error message on failure.
    """
    # try:
    #     1. pull the parent directory out of path (os.path)
    #     2. create it (os.makedirs + the "already exists is fine" flag)
    #     3. open path for writing, write the content
    #     4. return a confirmation with a byte count
    # except OSError:
    #     5. return the error as a string
    pass


def tool_run_command(command: str) -> str:
    """Execute a shell command. Returns stdout and stderr.

    The contract: always return a string — stdout and stderr labeled, on
    success and on failure. Use subprocess.run() with timeout=30 and
    capture_output=True.
    """
    # try:
    #     1. call subprocess.run with the flags above
    #     2. build one labeled string: "Output: ...\nErrors: ..."
    #     3. return it
    # except subprocess.TimeoutExpired:
    #     4. return the timeout as text
    pass


# --- Step 6b: Tool Registry (maps tool name → function) ---
# Maps tool names to their implementations
TOOL_IMPLS = {
    'read_file': tool_read_file,
    'write_file': tool_write_file,
    'run_command': tool_run_command,
}


# --- Step 1: Call the LLM ---

def call_llm(messages: list[dict]) -> object:
    """
    Send a conversation to the LLM via the openai library and return the
    response message object.

    messages: list of {"role": "user"|"assistant"|"system"|"tool", "content": "..."}
    Returns: the response message object (has .content and .tool_calls)
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )
    return response.choices[0].message


# --- Steps 6a–6b: The Agent Loop (YOU BUILD — the heart of the project) ---
# TODO: Implement the main agent loop

def run_agent(user_message: str) -> str:
    """
    Run the full agent loop:

    1. Start conversation with system prompt + user message
    2. Call the LLM (with tools)
    3. Check the response for tool_calls
    4. If tool calls found: execute them, add results to conversation, go to 2
    5. If no tool calls: return the response as the final answer
    6. Stop after MAX_ITERATIONS to prevent infinite loops
    """
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_message},
    ]

    # TODO: Implement the loop
    # 1. Loop up to MAX_ITERATIONS times
    # 2. Call call_llm(messages) to get the LLM response
    # 3. Append the response message to messages
    # 4. If the response has no tool_calls, return response.content
    # 5. For each tool call:
    #    - Get the tool name and arguments
    #    - Look up the implementation in TOOL_IMPLS
    #    - Execute it (catch errors and return error messages)
    #    - Append a {"role": "tool", "tool_call_id": ..., "content": result}
    # 6. If the loop exhausts, return "Max iterations reached"

    return "Agent loop not yet implemented"


# --- Self-Reload (Stage 3) ---
# If the agent modifies this file (write_file on harness.py), the change is
# detected and the process re-execs itself so the new tool takes effect on the
# next request. Without this, a running Python process never picks up edits to
# its own source.
SOURCE_FILE = os.path.abspath(__file__)
SOURCE_MTIME = os.path.getmtime(SOURCE_FILE)


def source_has_changed() -> bool:
    return os.path.getmtime(SOURCE_FILE) != SOURCE_MTIME


# --- Step 4: HTTP Endpoint (GIVEN) ---

class HarnessHandler(BaseHTTPRequestHandler):
    """HTTP handler that accepts POST /chat and returns agent responses."""

    def do_POST(self):
        if self.path != '/chat':
            self.send_error(404)
            return

        # Read and validate the request body
        try:
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length))
            user_message = body['message']
        except (KeyError, ValueError, TypeError):
            self.send_error(400, 'Bad request — expected JSON {"message": "..."}')
            return

        # Call the agent — never let an exception kill the connection
        try:
            response = run_agent(user_message)
        except Exception as e:
            response = f'Harness error: {e}'

        # Return the response as JSON
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"response": response}).encode())

        # Stage 3 — if the agent rewrote its own source, restart with the new code
        if source_has_changed():
            print('harness.py was modified — restarting with the new code...')
            os.execv(sys.executable, [sys.executable, SOURCE_FILE])

    def log_message(self, format, *args):
        """Override to print cleaner logs."""
        print(f'[{self.log_date_time_string()}] {format % args}')


# --- Main ---
def main():
    print(f'Starting Agent Harness on port {HARNESS_PORT}')
    print(f'Ollama URL: {OLLAMA_URL}')
    print(f'Model: {MODEL}')
    print(f'API key: {"custom (from MODEL_API_KEY)" if API_KEY != "ollama" else "placeholder (local Ollama)"}')
    print(f'Max iterations: {MAX_ITERATIONS}')
    print(f'Available tools: {", ".join(TOOL_IMPLS.keys())}')
    print()

    # ThreadingHTTPServer: a 3B model on CPU can take minutes per request —
    # a single-threaded server would block every other request meanwhile.
    server = ThreadingHTTPServer(('0.0.0.0', HARNESS_PORT), HarnessHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.shutdown()


if __name__ == '__main__':
    main()