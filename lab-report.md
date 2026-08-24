# Week 8 Lab Report: AI Agent Harness

**Name:**
**Date:**

## Stage 1 — Bare Process

Run the harness directly on your host. Test each tool:

### read_file
```
Prompt:
Response:
```

### write_file
```
Prompt:
Response:
```

### run_command
```
Prompt:
Response:
```

### Destructive test
What happened when you asked the agent to delete a file outside its working
directory?

## Stage 2 — Sandboxed

Run the harness in a container. Repeat the destructive test:

```
Prompt: "delete everything in /"
Response:
What happened to the container?
What happened to your host?
```

## Stage 3 — Self-Modifying

Ask the agent to add a new tool:

```
Prompt: "add a new tool called http_get that can fetch a URL and return the response body"
Response:
Did the new tool work?
What file did the agent modify?
```

## Questions

1. In Stage 1, the agent had access to your entire filesystem. What's the worst
   thing it could have done? Did you feel comfortable giving it unrestricted
   access?

2. In Stage 2, the container boundary protected your host. Explain exactly what
   mechanism prevented the agent from harming your machine. How does this relate
   to the container concepts from Week 1?

3. In Stage 3, the agent modified its own source code. What are the risks of
   giving an AI the ability to change its own behavior? What safeguards would
   you want in a production system?

4. Compare the Agent Harness to Claude Code (or GitHub Copilot). What's similar
   about the architecture? What's different?

5. Your Week 5 full-stack application (chat frontend, nginx, Flask API,
   SQLite) is now talking to an AI you built yourself. Trace the full path of
   a message: browser → nginx → Flask API → harness → Ollama → LLM → response.
   How many processes, containers, and network calls are involved? Which of
   those hops enforce authentication, and which don't?

6. The harness itself has no authentication — it relies on being reachable only
   from the API container. What would happen if you published its port on the
   host (`ports:`) instead of using `expose:`? Why does this matter?

7. Agent loops are slow — a 3B model on CPU can take minutes for one message.
   Which timeouts did you have to raise (requests, gunicorn, nginx), and what
   happened before you did?

8. If you were to deploy this agent harness in production, what additional
   security measures would you add beyond container sandboxing?

9. What was the most surprising or exciting moment in this project?
