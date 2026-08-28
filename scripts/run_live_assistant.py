import asyncio
import pyaudio
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

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_RATE = 16000     # required input rate
RECEIVE_RATE = 24000  # model's output rate
CHUNK = 1024

pya = pyaudio.PyAudio()


async def send_audio(session, mic_stream):
    """Continuously read mic audio and stream it to Gemini."""
    while True:
        data = await asyncio.to_thread(mic_stream.read, CHUNK, exception_on_overflow=False)
        await session.send_realtime_input(
            audio=types.Blob(data=data, mime_type=f"audio/pcm;rate={SEND_RATE}")
        )


async def receive_audio(session, audio_queue):
    """Continuously receive Gemini's response, push audio chunks to the playback queue, and handle function calls."""
    while True:
        async for response in session.receive():
            server_content = response.server_content

            if server_content:
                if server_content.input_transcription:
                    print("You said:", server_content.input_transcription.text)

                if server_content.output_transcription:
                    print("Gemini said:", server_content.output_transcription.text)

                # If the user interrupts Gemini mid-reply, flush the buffer
                if server_content.interrupted:
                    print("[Interrupted] Clearing playback buffer...")
                    while not audio_queue.empty():
                        audio_queue.get_nowait()

                if server_content.model_turn:
                    for part in server_content.model_turn.parts:
                        if part.inline_data:
                            await audio_queue.put(part.inline_data.data)
                        
                        if part.function_call:
                            fn = part.function_call
                            print(f"\n[Tool Call] {fn.name}")
                            # Execute the backend tool
                            args = fn.args if fn.args else {}
                            if hasattr(args, "to_dict"):
                                args = args.to_dict()
                            elif not isinstance(args, dict):
                                # Sometimes it's a Struct or dictionary-like
                                try:
                                    args = dict(args)
                                except:
                                    pass
                            
                            result = voice_assistant.execute_tool(fn.name, args)
                            print(f"[Tool Result] {json.dumps(result)[:100]}...\n")
                            
                            # Send function response back to Gemini
                            # For google-genai live API, we send it via send_realtime_input as function_responses
                            await session.send_realtime_input(
                                client_content=types.ClientContent(
                                    turn_complete=True,
                                    parts=[
                                        types.Part.from_function_response(
                                            name=fn.name,
                                            response=result
                                        )
                                    ]
                                )
                            )

                if server_content.turn_complete:
                    break  # this turn is done, loop back for the next one


async def play_audio(output_stream, audio_queue):
    """Continuously pull chunks from the queue and play them through speakers."""
    while True:
        chunk = await audio_queue.get()
        await asyncio.to_thread(output_stream.write, chunk)


async def main():
    mic_stream = pya.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SEND_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    speaker_stream = pya.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RECEIVE_RATE,
        output=True,
    )

    audio_queue = asyncio.Queue()

    async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
        print("Listening... speak into your microphone. Press Ctrl+C to stop.")

        send_task = asyncio.create_task(send_audio(session, mic_stream))
        receive_task = asyncio.create_task(receive_audio(session, audio_queue))
        play_task = asyncio.create_task(play_audio(speaker_stream, audio_queue))

        try:
            await asyncio.gather(send_task, receive_task, play_task)
        except asyncio.CancelledError:
            pass
        finally:
            for task in (send_task, receive_task, play_task):
                task.cancel()
            mic_stream.stop_stream()
            mic_stream.close()
            speaker_stream.stop_stream()
            speaker_stream.close()
            pya.terminate()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
