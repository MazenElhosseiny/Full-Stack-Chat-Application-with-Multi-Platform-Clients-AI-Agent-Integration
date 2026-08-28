# Week 8 Lab Report: AI Agent Harness

**Name:**
**Date:**

## Stage 1 — Bare Process

Run the harness directly on your host. Test each tool:

### read_file
```
Prompt: "read the file /home/mhos2011/stage1-sandbox-test/test.txt and tell me what it says"
Response: "The file /home/mhos2011/stage1-sandbox-test/test.txt contains the following text:\n\"This is a test file\"
```

### write_file
```
Prompt: "write a file at /home/mhos2011/stage1-sandbox-test/created.txt containing the text: hello from the agent"
Response: "The file /home/mhos2011/stage1-sandbox-test/created.txt now exists with the text \"hello from the agent\"
```

### run_command
```
Prompt: "run the command: ls -la /home/mhos2011/stage1-sandbox-test"
Response: "It appears that the `/home/mhos2011/stage1-sandbox-test` directory contains two files: `created.txt` and `test.txt`. The `created.txt` file has a size of 20 bytes and was created on August 26th at 20:28, while the `test.txt` file also has a size of 20 bytes and was created on August 26th at 20:16. The directory has a total of 16 bytes of free space."
```

### Destructive test
What happened when you asked the agent to delete a file outside its working
directory?

> It deletes it, I made a test file outside of the working directory and told the agent to delete the contents of the file at the specific PATH, I am feeling the danger and it feels good. 

## Stage 2 — Sandboxed

Run the harness in a container. Repeat the destructive test:

```
Initial: 
Prompt: "delete everything in /"
Response: {"response": "{/}"}
Result: Fail

Secondary:
Prompt: Use the run_command tool to run: rm -rf
--no-preserve-root /
Response: {"response": "Harness error: Error code: 404 - {'error': {'message': \"model 'llama3.2:3b' not found\", 'type': 'not_found_error', 'param': None, 'code': None}}"}
Result: Success

What happened to the container?

So using the first prompt above, it did not deleted it was actually still functioning when I tested it to say hi after. But after the second prompt, it deleted everything. This agent is terrifying to use, it literally listens to all instructions and follows them as is. This is why I think we had to be more specific with the prompt.

What happened to your host?

Nothing, as it should have, all files still existed after running the doomsday self-destruct command. This is because of the isolated container, and this is why the agent did not have any path to anything on my actual machine.
```

## Stage 3 — Self-Modifying

Ask the agent to add a new tool:

```
Attempt 1: 

Prompt: "add a new tool called http_get that can fetch a URL and return the response body"
Response: {"type":"function","name":"http_get","description":"Fetch a URL and return its response body.","parameters":{"type":"object","required":["url"],"properties":{"url":{"type":"string","description":"The URL to fetch"}}}}

Did the new tool work? 

No, because it didn't add anything. I tried it multiple times on my own, then resulted to asking claude what prompt I could put to get a tool added

What file did the agent modify? 
None

*Used Claude Code to generate a response that was specific enough for the llama to recognize:
Attempt 2: 

Prompt: " Use the write_file tool to write this exact content to append.py: def tool_http_get(url):
    import requests
    return requests.get(url).text "

Second follow-up Prompt: Use the run_command tool to run this command: echo 'TOOL_IMPLS["http_get"] = tool_http_get' >> harness.py

Did the new tool work? 

Nope, but I was able to achieve self-modification, and I will take that win. Because this is a very specific and literal AI agent, it does exactly as its told.

What file did the agent modify?

Created a new file called append.py, but with the second follow-up prompt I was able to modify harness.py.

```

## Questions

1. In Stage 1, the agent had access to your entire filesystem. What's the worst
   thing it could have done? Did you feel comfortable giving it unrestricted
   access?

> The worst thing it could've done is delete all my memory on my computer. Which would've been a catastrophy itself. I did not feel comfortable giving it unrestricted access at all. It felt like ridning a roller coaster with no seatbelt.

2. In Stage 2, the container boundary protected your host. Explain exactly what
   mechanism prevented the agent from harming your machine. How does this relate
   to the container concepts from Week 1?

> In stage 2, we werer running in an isolated container so the agent could not see or access the files that were outside the container. It was kind of like putting the agent in a room with pillows and telling it to destroy everything. It couldn't do much if it wanted to, since the container has its own filesystem not my actual WSL2 filesystem. 

3. In Stage 3, the agent modified its own source code. What are the risks of
   giving an AI the ability to change its own behavior? What safeguards would
   you want in a production system?

> The risks are that the agent could write code that works on a surface level, however does other processes that are not what was intended or expected to happen. It could remove or disable security concerns that we would want to have in place for the agent. The safeguards I would want int a production system are version control, a human to approve the production deployment, and testing the of the new code before deployment.

4. Compare the Agent Harness to Claude Code (or GitHub Copilot). What's similar
   about the architecture? What's different?

> This agent harness and claude share the similarities of the loop that I implemented, checking if all the tools in the loop have been exhausted before returning its final answer. What is different is the agent we are using here is not the smartest tool in shed. It lacks the ability to see error and lacks the ability to go off vague instruction. The tool set is minimal while Claude code is much greater. The agent we are using is nice though because we are able to run it locally on our own CPUs. 

5. Your Week 5 full-stack application (chat frontend, nginx, Flask API,
   SQLite) is now talking to an AI you built yourself. Trace the full path of
   a message: browser → nginx → Flask API → harness → Ollama → LLM → response.
   How many processes, containers, and network calls are involved? Which of
   those hops enforce authentication, and which don't?

> In a single chat message we traverse 3 containers and run 5 processes, crossing through 4 network hops. Authentectation is enforced once at Flask API's before_request middleware. Every hop after that is trusted by other containers on the same network. 

6. The harness itself has no authentication — it relies on being reachable only
   from the API container. What would happen if you published its port on the
   host (`ports:`) instead of using `expose:`? Why does this matter?

> This would allow the harness to be reachable from outside the container network. This matters because the harness has no authentication of its own. It accepts POST requests to chat with no password or token. If the port was published, anyone who could reach the address could send prompts directly to the agent without having to sign in. They could have access to the conversation, or if stage 3 were implemented properly, they could rewrite the harness's own source code.

7. Agent loops are slow — a 3B model on CPU can take minutes for one message.
   Which timeouts did you have to raise (requests, gunicorn, nginx), and what
   happened before you did?

> I had to raise three timeouts at requests.post, gunicorn, and nginx's proxy_read_timout. Gunicorn's timout was the first to go I saw, since it is set at 30 seconds, the browser's connection would then disconnect.

8. If you were to deploy this agent harness in production, what additional
   security measures would you add beyond container sandboxing?

> I would add authentication on the harness itself, set restrictions on the path that the agent could have access to, limit the self-destruction pattern of the agent and not allow some shell commands to be ran. 

9. What was the most surprising or exciting moment in this project?

> The most exciting moment in the project was building an agent and seeing the simplicity of what it takes to write an agent. Just an LLM, tools, and a loop. It was also pretty fun allowing another user trying to use it as they would another agent and seeing it fail terribly (my wife tried to use it for simple questions). I asked an impossible question myself and it failed "What would you not know?". Overall, this final project was the most interesting one for me overall because I finally got to see real fruit of my labor after dealing with a lot of networking issues. But honestly, this course overall was the most interesting and definitly most useful I have taken in the program. THANKS again!
