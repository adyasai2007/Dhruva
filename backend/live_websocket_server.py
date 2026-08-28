"""
DHRUVA — Live Audio WebSocket Streaming Bridge for Gemini Live API.
Powered by Google GenAI Live API (gemini-3.1-flash-live-preview).

Provides a high-speed, bidirectional PCM audio streaming server over WebSockets (ws://0.0.0.0:8001).
Bridges client-side Web Audio (16kHz PCM) with Gemini Live, executes cultural database tools in real-time,
and returns low-latency 24kHz synthesized audio and navigation directives to the frontend UI.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import websockets
from google import genai
from google.genai import types

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.services.voice_assistant import (
    SYSTEM_INSTRUCTION,
    VOICE_TOOL_DECLARATIONS,
    voice_assistant,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dhruva.live_websocket")

MODEL = "gemini-3.1-flash-live-preview"

CONFIG: Dict[str, Any] = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {},
    "input_audio_transcription": {},
    "system_instruction": SYSTEM_INSTRUCTION,
    "tools": [{"function_declarations": VOICE_TOOL_DECLARATIONS}],
}


def get_genai_client() -> genai.Client:
    """Instantiate GenAI Client using configured environment API key."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set. Live connection may fail.")
        return genai.Client()
    return genai.Client(api_key=api_key)


async def handle_tool_call(
    session: Any,
    websocket: websockets.WebSocketServerProtocol,
    tool_call: types.LiveServerToolCall,
) -> None:
    """Execute tools requested by Gemini Live model against the local database repository."""
    function_responses: List[types.FunctionResponse] = []

    for fn in tool_call.function_calls or []:
        logger.info(f"[Tool Call] Gemini invoking: {fn.name} with args {fn.args}")

        # Notify frontend client about the active tool execution
        try:
            await websocket.send(json.dumps({"type": "tool_call", "name": fn.name}))
        except Exception:
            pass

        # Normalize arguments
        args: Dict[str, Any] = {}
        if fn.args:
            if hasattr(fn.args, "to_dict"):
                args = fn.args.to_dict()
            elif isinstance(fn.args, dict):
                args = fn.args
            else:
                try:
                    args = dict(fn.args)
                except Exception:
                    args = {}

        # Execute tool against DHRUVA database and itinerary engine
        result = voice_assistant.execute_tool(fn.name, args)

        # Dispatch navigation directives to frontend (modals, itinerary page view, etc.)
        if isinstance(result, dict) and result.get("action") in ("navigate_ui", "open_modal", "view_itinerary"):
            try:
                await websocket.send(json.dumps({"type": "navigation", "data": result}))
            except Exception:
                pass

        fn_id = getattr(fn, "id", None) or "call_1"
        function_responses.append(
            types.FunctionResponse(
                name=fn.name,
                id=fn_id,
                response=result if isinstance(result, dict) else {"result": result},
            )
        )

    if function_responses:
        logger.info(f"Returning {len(function_responses)} tool response(s) to Gemini Live")
        await session.send_tool_response(function_responses=function_responses)


async def handle_client(websocket: websockets.WebSocketServerProtocol) -> None:
    """Handle an incoming client WebSocket connection and bridge it to a Gemini Live session."""
    client_ip = getattr(websocket, "remote_address", ("unknown", 0))[0]
    logger.info(f"Client connected from {client_ip}")

    client = get_genai_client()

    try:
        async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            logger.info("Gemini Live bidirectional session established successfully.")

            async def receive_from_client() -> None:
                """Read audio chunks or text messages from the browser and send to Gemini."""
                try:
                    async for message in websocket:
                        if isinstance(message, bytes):
                            # Binary PCM audio buffer (16kHz mono)
                            await session.send_realtime_input(
                                audio=types.Blob(data=message, mime_type="audio/pcm;rate=16000")
                            )
                        elif isinstance(message, str):
                            # Text prompt (e.g. from quick suggestion pills)
                            logger.info(f"Browser sent text query: {message}")
                            await session.send_client_content(
                                turns=[types.Content(parts=[types.Part.from_text(text=message)])],
                                turn_complete=True,
                            )
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Client WebSocket closed in receive_from_client.")
                except Exception as e:
                    logger.warning(f"Exception in receive_from_client: {e}")

            async def receive_from_gemini() -> None:
                """Continuously stream responses from Gemini back to the browser."""
                try:
                    while True:
                        received_turn_item = False
                        async for response in session.receive():
                            received_turn_item = True

                            # 1. Process Tool Calls (function execution)
                            if response.tool_call:
                                await handle_tool_call(session, websocket, response.tool_call)

                            # 2. Process Server Content (audio chunks and transcriptions)
                            if response.server_content:
                                sc = response.server_content

                                # User speech transcription
                                if sc.input_transcription and sc.input_transcription.text:
                                    await websocket.send(json.dumps({
                                        "type": "transcript",
                                        "role": "user",
                                        "text": sc.input_transcription.text,
                                    }))

                                # Gemini speech transcription
                                if sc.output_transcription and sc.output_transcription.text:
                                    await websocket.send(json.dumps({
                                        "type": "transcript",
                                        "role": "gemini",
                                        "text": sc.output_transcription.text,
                                    }))

                                # Interruption detection
                                if sc.interrupted:
                                    logger.info("User interrupted model speech mid-turn.")
                                    await websocket.send(json.dumps({"type": "interrupted"}))

                                # Synthesized Audio
                                if sc.model_turn:
                                    for part in sc.model_turn.parts or []:
                                        if part.inline_data and part.inline_data.data:
                                            # Send raw 24kHz PCM audio binary directly to browser
                                            await websocket.send(part.inline_data.data)

                                if sc.turn_complete:
                                    # Current turn finished; break inner generator to await next turn
                                    break

                        if not received_turn_item:
                            logger.info("Gemini stream closed or completed.")
                            break

                except websockets.exceptions.ConnectionClosed:
                    logger.info("Client WebSocket closed in receive_from_gemini.")
                except Exception as e:
                    logger.error(f"Gemini streaming exception: {e}")

            # Run both streaming directions concurrently; cancel immediately when either disconnects
            client_task = asyncio.create_task(receive_from_client())
            gemini_task = asyncio.create_task(receive_from_gemini())

            done, pending = await asyncio.wait(
                [client_task, gemini_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.debug(f"Error cancelling task: {e}")

    except Exception as e:
        logger.error(f"Gemini session lifecycle error: {e}", exc_info=True)
        try:
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e),
            }))
        except Exception:
            pass
    finally:
        logger.info("Client session handler finalized.")


async def main() -> None:
    host = "0.0.0.0"
    port = 8001
    logger.info(f"Starting DHRUVA Gemini Live Audio WebSocket Server on ws://{host}:{port}...")
    async with websockets.serve(handle_client, host, port):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped by user.")
