import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
APP_NAME = "my_agent_ui"

# Load agent credentials before importing the agent module.
load_dotenv(BASE_DIR / "my_agent" / ".env", override=True)

from my_agent.agent import root_agent

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")
session_service = InMemorySessionService()
runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)
created_sessions: set[tuple[str, str]] = set()


def ensure_session(user_id: str, session_id: str) -> None:
    """Create an ADK session once per (user_id, session_id)."""
    key = (user_id, session_id)
    if key in created_sessions:
        return

    import asyncio

    asyncio.run(
        session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
    )
    created_sessions.add(key)


def ask_agent(user_id: str, session_id: str, prompt: str) -> str:
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    import asyncio

    async def run_async() -> str:
        text_parts: list[str] = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            content = getattr(event, "content", None)
            if not content or not getattr(content, "parts", None):
                continue

            for part in content.parts:
                text = getattr(part, "text", None)
                if text:
                    text_parts.append(text)

        return "\n".join(text_parts).strip()

    response_text = asyncio.run(run_async())
    return response_text or "I could not generate a response."


@app.get("/")
def index() -> object:
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/<path:filename>")
def static_files(filename: str) -> object:
    file_path = WEB_DIR / filename
    if file_path.exists() and file_path.is_file():
        return send_from_directory(WEB_DIR, filename)
    return send_from_directory(WEB_DIR, "index.html")


@app.post("/api/session")
def create_session() -> object:
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("userId") or "local-user"
    session_id = str(uuid.uuid4())

    ensure_session(user_id, session_id)
    return jsonify({"userId": user_id, "sessionId": session_id})


@app.post("/api/chat")
def chat() -> object:
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    user_id = payload.get("userId") or "local-user"
    session_id = payload.get("sessionId") or str(uuid.uuid4())

    if not message:
        return jsonify({"error": "Message is required."}), 400

    try:
        ensure_session(user_id, session_id)
        reply = ask_agent(user_id=user_id, session_id=session_id, prompt=message)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Agent error: {exc}"}), 500

    return jsonify({
        "userId": user_id,
        "sessionId": session_id,
        "reply": reply,
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=True)
