# main.py
import os
import subprocess
import tempfile
import requests
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Read OpenRouter API key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat"

# 1. RUN CODE ENDPOINT (with Docker security)
@app.post("/run")
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")

    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as tmp:
        tmp.write(code)
        tmp.flush()

        # Run the code in a Docker container (python:3.10-slim)
        container_command = [
            "docker", "run", "--rm",
            "--cpus=0.5", "--memory=128m",
            "-v", f"{tmp.name}:/app/code.py",
            "python:3.10-slim",
            "python", "/app/code.py"
        ]

        try:
            result = subprocess.run(
                container_command,
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"error": "⏰ Execution timed out."}
        except Exception as e:
            return {"error": f"❌ Docker execution failed: {str(e)}"}

# 2. ASK-AI ENDPOINT USING OPENROUTER + DEEPSEEK
class PromptRequest(BaseModel):
    prompt: str
    user_code: str = ""

@app.post("/ask-ai")
def ask_ai(req: PromptRequest):
    full_prompt = f"""You are a helpful coding assistant.
The user is writing the following code:

```python
{req.user_code}
```

Now respond to the user's query:
{req.prompt}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000"  # Update this on deployment
    }

    data = {
        "model": "deepseek-coder:6.7b-instruct-v3",
        "messages": [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": full_prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=30)
        if response.ok:
            result = response.json()
            ai_reply = result["choices"][0]["message"]["content"]
            return {"response": ai_reply}
        else:
            return {"response": f"⚠️ Error: {response.text}"}
    except Exception as e:
        return {"response": f"⚠️ Exception: {str(e)}"}

