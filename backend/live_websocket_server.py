import asyncio
import websockets
import json
import os
import sys
from pathlib import Path
from google import genai
from google.genai import types

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.voice_assistant import voice_assistant, VOICE_TOOL_DECLARATIONS, SYSTEM_INSTRUCTION

API_KEY = os.getenv("GEMINI_API_KEY", "")

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-3.1-flash-live-preview"

CONFIG = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {},
    "input_audio_transcription": {},
    "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
    "tools": [{"function_declarations": VOICE_TOOL_DECLARATIONS}]
}

async def handle_tool_call(session, websocket, tool_call):
    """Execute tools triggered by Gemini and return responses."""
    function_responses = []
    for fn in tool_call.function_calls:
        print(f"[Tool Call] Gemini executing: {fn.name} with args {fn.args}")
        try:
            await websocket.send(json.dumps({"type": "tool_call", "name": fn.name}))
        except Exception:
            pass

        args = fn.args if fn.args else {}
        if hasattr(args, "to_dict"):
            args = args.to_dict()
        elif not isinstance(args, dict):
            try:
                args = dict(args)
            except Exception:
                pass

        # Execute against local DB
        result = voice_assistant.execute_tool(fn.name, args)

        # Send UI navigation events to browser if returned
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
                response=result if isinstance(result, dict) else {"result": result}
            )
        )

    if function_responses:
        await session.send_tool_response(function_responses=function_responses)


async def handle_client(websocket):
    print("Client connected from browser!")
    try:
        async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            print("Gemini Live Session initialized successfully.")

            async def receive_from_client():
                """Receive raw PCM audio or text from the browser and send to Gemini."""
                try:
                    async for message in websocket:
                        if isinstance(message, bytes):
                            await session.send_realtime_input(
                                audio=types.Blob(data=message, mime_type="audio/pcm;rate=16000")
                            )
                        else:
                            print(f"Browser sent text: {message}")
                            await session.send_client_content(
                                turns=[types.Content(parts=[types.Part.from_text(text=message)])],
                                turn_complete=True
                            )
                except websockets.exceptions.ConnectionClosed:
                    print("Browser client closed WebSocket connection.")
                except Exception as e:
                    print(f"Error in client send loop: {e}")

            async def receive_from_gemini():
                """Continuously receive Gemini's response across all turns and tool calls."""
                try:
                    while True:
                        async for response in session.receive():
                            # 1. Handle Tool Calls (critical for multi-turn conversations with tool execution)
                            if response.tool_call:
                                await handle_tool_call(session, websocket, response.tool_call)

                            # 2. Handle Server Content (speech audio & live transcriptions)
                            if response.server_content:
                                sc = response.server_content

                                if sc.input_transcription and sc.input_transcription.text:
                                    await websocket.send(json.dumps({
                                        "type": "transcript",
                                        "role": "user",
                                        "text": sc.input_transcription.text
                                    }))

                                if sc.output_transcription and sc.output_transcription.text:
                                    await websocket.send(json.dumps({
                                        "type": "transcript",
                                        "role": "gemini",
                                        "text": sc.output_transcription.text
                                    }))

                                if sc.interrupted:
                                    await websocket.send(json.dumps({"type": "interrupted"}))

                                if sc.model_turn:
                                    for part in sc.model_turn.parts:
                                        if part.inline_data:
                                            # Send raw audio directly as bytes (24kHz PCM)
                                            await websocket.send(part.inline_data.data)

                                if sc.turn_complete:
                                    # Current turn complete; break inner loop to immediately await next turn
                                    break
                except websockets.exceptions.ConnectionClosed:
                    print("Client disconnected during Gemini stream.")
                except Exception as e:
                    print(f"Gemini streaming exception: {e}", file=sys.stderr)

            await asyncio.gather(receive_from_client(), receive_from_gemini())

    except Exception as e:
        print(f"Gemini session lifecycle error: {e}", file=sys.stderr)
        try:
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except Exception:
            pass


async def main():
    print("Starting Dhruva Live Audio WebSocket Server on ws://localhost:8001...")
    async with websockets.serve(handle_client, "0.0.0.0", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
