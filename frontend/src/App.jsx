import { useState, useRef, useEffect } from 'react'
import { useGeminiLive } from './hooks/useGeminiLive'
import './index.css'

const VOICES = ["Aoede", "Puck", "Charon", "Fenrir", "Kore"];

function App() {
  const [voice, setVoice] = useState("Aoede");
  const { isConnected, connect, disconnect, logs } = useGeminiLive(voice);
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="app-container">
      <header className="glass-header">
        <h1>Travel Agent Live</h1>
        <div className="controls">
          <select 
            value={voice} 
            onChange={e => setVoice(e.target.value)}
            disabled={isConnected}
            className="voice-select"
          >
            {VOICES.map(v => <option key={v} value={v}>{v}</option>)}
          </select>
          <button 
            className={`btn ${isConnected ? 'btn-danger' : 'btn-primary'}`}
            onClick={isConnected ? disconnect : connect}
          >
            {isConnected ? 'Disconnect' : 'Connect'}
          </button>
        </div>
      </header>

      <main className="main-content">
        <div className={`status-indicator ${isConnected ? 'active' : ''}`}>
          <div className="waveform">
            <div className="bar"></div>
            <div className="bar"></div>
            <div className="bar"></div>
            <div className="bar"></div>
          </div>
          <h2>{isConnected ? "Listening & Speaking..." : "Disconnected"}</h2>
          <p>{isConnected ? "Say 'Hi' to get started with your travel plans!" : "Select a voice and click connect."}</p>
        </div>

        <div className="logs-container glass-panel">
          <h3>Activity Log</h3>
          <div className="logs">
            {logs.length === 0 && <span className="empty-log">No activity yet.</span>}
            {logs.map((log, i) => (
              <div key={i} className={`log-entry ${log.type}`}>
                <span className="log-time">[{log.time}]</span>
                <span className="log-msg">{log.msg}</span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
