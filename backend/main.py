import os
import json
import logging
import asyncio
import uuid
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import websockets
from langfuse import Langfuse

from config import GEMINI_API_KEY, MODEL, SYSTEM_INSTRUCTION
from tools import MOCK_TOOLS, handle_tool_call

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Langfuse SDK
if not os.getenv("LANGFUSE_PUBLIC_KEY"):
    logger.warning("No Langfuse credentials found in .env. Tracing to Langfuse dashboard is disabled. Terminal logs will still be printed.")
langfuse = Langfuse()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HOST = "generativelanguage.googleapis.com"
GEMINI_WS_URL = f"wss://{HOST}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={GEMINI_API_KEY}"

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to proxy")
    
    session_id = str(uuid.uuid4())
    trace = langfuse.trace(
        name="travel-voice-session",
        session_id=session_id,
        user_id="web-user"
    )
    trace.event(name="Session Started")
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        logger.error("GEMINI_API_KEY is missing or invalid.")
        trace.event(name="Error", input={"message": "Missing GEMINI_API_KEY"})
        langfuse.flush()
        await websocket.send_text(json.dumps({"error": "Missing GEMINI_API_KEY"}))
        await websocket.close(code=1011, reason="API Key Error")
        return

    try:
        async with websockets.connect(GEMINI_WS_URL) as gemini_ws:
            logger.info("Connected to Gemini Live API")
            trace.event(name="Connected to Gemini API")
            
            state = {
                "audio_streaming_span": None,
                "audio_streaming_start": None,
                "audio_playback_span": None,
                "audio_playback_start": None,
                "gemini_processing_span": None
            }
            
            def end_all_spans():
                now = datetime.utcnow()
                if state["audio_streaming_span"]:
                    duration = (now - state["audio_streaming_start"]).total_seconds() * 1000
                    state["audio_streaming_span"].end(end_time=now)
                    logger.info(f"[Tracing] Ended Audio Streaming Span (Interrupted) - {duration:.0f}ms")
                    state["audio_streaming_span"] = None
                if state["audio_playback_span"]:
                    duration = (now - state["audio_playback_start"]).total_seconds() * 1000
                    state["audio_playback_span"].end(end_time=now)
                    logger.info(f"[Tracing] Ended Audio Playback Span (Interrupted) - {duration:.0f}ms")
                    state["audio_playback_span"] = None
                if state["gemini_processing_span"]:
                    state["gemini_processing_span"].end(end_time=now)
                    state["gemini_processing_span"] = None
            
            async def forward_to_gemini():
                try:
                    # Expect first message to be setup
                    first_msg = await websocket.receive_text()
                    parsed_first = json.loads(first_msg)
                    voice = parsed_first.get("voice", "Aoede")
                    
                    setup_payload = {
                        "setup": {
                            "model": MODEL,
                            "generationConfig": {
                                "responseModalities": ["AUDIO"],
                                "speechConfig": {
                                    "voiceConfig": {
                                        "prebuiltVoiceConfig": {
                                            "voiceName": voice
                                        }
                                    }
                                }
                            },
                            "systemInstruction": SYSTEM_INSTRUCTION,
                            "tools": MOCK_TOOLS
                        }
                    }
                    await gemini_ws.send(json.dumps(setup_payload))
                    logger.info(f"Sent setup to Gemini with voice: {voice}")
                    trace.event(name="Setup Completed", input={"voice": voice, "model": MODEL})

                    while True:
                        data = await websocket.receive_text()
                        
                        if state["audio_streaming_span"] is None and state["audio_playback_span"] is None:
                            logger.info("[Tracing] Started Audio Streaming Span")
                            now = datetime.utcnow()
                            state["audio_streaming_start"] = now
                            state["audio_streaming_span"] = trace.span(
                                name="Audio Streaming",
                                start_time=now
                            )
                            
                        await gemini_ws.send(data)
                        
                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                    trace.event(name="Client Disconnected")
                except Exception as e:
                    logger.error(f"Error forwarding to Gemini: {e}")
                    trace.event(name="Error", input={"message": str(e), "direction": "to_gemini"})
            
            async def forward_to_client():
                try:
                    async for message in gemini_ws:
                        if isinstance(message, bytes):
                            message = message.decode("utf-8")
                        parsed = json.loads(message)
                        now = datetime.utcnow()
                        
                        if "serverContent" in parsed:
                            content = parsed["serverContent"]
                            if content.get("interrupted"):
                                logger.info("Model was interrupted by user (Barge-in)")
                                trace.event(name="User Barge-In", input={"status": "interrupted"})
                                end_all_spans()
                            
                            elif "modelTurn" in content:
                                if state["audio_streaming_span"]:
                                    duration = (now - state["audio_streaming_start"]).total_seconds() * 1000
                                    state["audio_streaming_span"].end(end_time=now)
                                    logger.info(f"[Tracing] Ended Audio Streaming Span - {duration:.0f}ms")
                                    state["audio_streaming_span"] = None
                                    
                                    # Mark Gemini processing completion
                                    trace.span(
                                        name="Gemini Processing",
                                        start_time=now,
                                        end_time=now,
                                        input={"status": "First Token Generated"}
                                    )
                                    logger.info(f"[Tracing] Logged Gemini Processing Marker (Time-To-First-Token: {duration:.0f}ms)")
                                
                                if not state["audio_playback_span"]:
                                    logger.info("[Tracing] Started Audio Playback Span")
                                    state["audio_playback_start"] = now
                                    state["audio_playback_span"] = trace.span(
                                        name="Audio Playback",
                                        start_time=now
                                    )
                                    
                            elif content.get("turnComplete"):
                                if state["audio_playback_span"]:
                                    duration = (now - state["audio_playback_start"]).total_seconds() * 1000
                                    state["audio_playback_span"].end(end_time=now)
                                    logger.info(f"[Tracing] Ended Audio Playback Span - {duration:.0f}ms")
                                    state["audio_playback_span"] = None
                                    
                        elif "toolCall" in parsed:
                            logger.info("Model triggered a tool call")
                            tool_calls = parsed["toolCall"].get("functionCalls", [])
                            for tc in tool_calls:
                                logger.info(f"Executing tool: {tc.get('name')}")
                                
                                # Trace tool execution in Langfuse
                                span = trace.span(
                                    name=f"Tool Call: {tc.get('name')}",
                                    input=tc
                                )
                                
                                response_payload = handle_tool_call(tc)
                                
                                if response_payload:
                                    span.update(output=response_payload)
                                    span.end()
                                    
                                    await gemini_ws.send(json.dumps(response_payload))
                                    logger.info(f"Sent tool response for {tc.get('name')}")
                        
                        await websocket.send_text(message)
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Gemini WebSocket closed")
                    trace.event(name="Gemini Connection Closed")
                except Exception as e:
                    logger.error(f"Error forwarding to client: {e}")
                    trace.event(name="Error", input={"message": str(e), "direction": "to_client"})
            
            await asyncio.gather(
                forward_to_gemini(),
                forward_to_client()
            )
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        trace.event(name="Connection Error", input={"error": str(e)})
        await websocket.close(code=1011)
    finally:
        # Critical: flush traces asynchronously before closing
        langfuse.flush()

def main():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

if __name__ == "__main__":
    main()
