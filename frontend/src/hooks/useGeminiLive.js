import { useState, useRef, useCallback } from 'react';
import { AudioRecorder } from '../audio/audio_recorder';
import { AudioPlayer } from '../audio/audio_player';

export function useGeminiLive(voice = "Aoede") {
  const [isConnected, setIsConnected] = useState(false);
  const [logs, setLogs] = useState([]);
  const wsRef = useRef(null);
  const recorderRef = useRef(null);
  const playerRef = useRef(null);

  const addLog = useCallback((msg, type = "info") => {
    setLogs(prev => [...prev, { msg, type, time: new Date().toLocaleTimeString() }]);
  }, []);

  const connect = useCallback(async () => {
    if (wsRef.current) return;
    addLog("Connecting to proxy on port 8001...", "sys");
    
    playerRef.current = new AudioPlayer();
    
    wsRef.current = new WebSocket("ws://localhost:8001/ws");
    
    wsRef.current.onopen = async () => {
      setIsConnected(true);
      addLog(`Connected! Configured voice: ${voice}`, "sys");
      wsRef.current.send(JSON.stringify({ voice }));
      
      recorderRef.current = new AudioRecorder((base64) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            realtimeInput: {
              mediaChunks: [{ mimeType: "audio/pcm;rate=16000", data: base64 }]
            }
          }));
        }
      });
      await recorderRef.current.start();
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.serverContent) {
        if (data.serverContent.interrupted) {
          addLog("Barge-in detected: Agent audio interrupted", "warn");
          playerRef.current?.interrupt();
        }
        const modelTurn = data.serverContent.modelTurn;
        if (modelTurn && modelTurn.parts) {
          modelTurn.parts.forEach(part => {
            if (part.text) addLog(`Agent: ${part.text}`, "agent");
            if (part.inlineData && part.inlineData.mimeType.startsWith("audio/pcm")) {
              playerRef.current?.play(part.inlineData.data);
            }
          });
        }
      } else if (data.toolCall) {
        const calls = data.toolCall.functionCalls || [];
        calls.forEach(c => addLog(`Server Executing Tool: ${c.name}`, "tool"));
      } else if (data.error) {
        addLog(`Error: ${data.error}`, "error");
      }
    };
    
    wsRef.current.onclose = (e) => {
      setIsConnected(false);
      addLog(`Disconnected (Code: ${e.code})`, "sys");
      recorderRef.current?.stop();
      wsRef.current = null;
    };
  }, [voice, addLog]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  return { isConnected, connect, disconnect, logs };
}
