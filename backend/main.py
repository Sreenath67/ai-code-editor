# main.py
import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter key for AI model
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# 1. RUN CODE USING PISTON API
@app.post("/run")
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")

    try:
        res = requests.post("https://emkc.org/api/v2/piston/execute", json={
            "language": "python3",
            "version": "*",
            "files": [
                {
                    "name": "main.py",
                    "content": code
                }
            ]
        }, timeout=10)

        if res.ok:
            result = res.json()
            return {
                "stdout": result.get("run", {}).get("output", ""),
                "stderr": "" if result.get("run", {}).get("output") else "Error running code."
            }
        else:
            return {"error": f"⚠️ Piston Error: {res.text}"}
    except Exception as e:
        return {"error": f"⚠️ Request failed: {str(e)}"}


# 2. AI CHAT USING OPENROUTER
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
        "HTTP-Referer": "https://ai-code-editor.vercel.app"
    }

    data = {
        "model": "openchat/openchat-3.5-1210",
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

    