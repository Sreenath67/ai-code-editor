// App.js
import React, { useState, useRef } from "react";
import Editor from "@monaco-editor/react";
import "./App.css";

function App() {
  const [code, setCode] = useState(`print("Hello, World!")`);
  const [output, setOutput] = useState("");
  const [chatLog, setChatLog] = useState([]);
  const [promptInput, setPromptInput] = useState("");
  const [isListening, setIsListening] = useState(false);
  const editorRef = useRef(null);

  const BACKEND_URL = "https://ai-code-editor-2.onrender.com"; // Railway backend URL
   // Railway backend URL
  // Voice recognition setup
  const recognitionRef = useRef(null);

  const handleMicClick = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser.');
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!recognitionRef.current) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setPromptInput(prev => prev + (prev ? ' ' : '') + transcript);
        setIsListening(false);
      };
      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };
      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
    setIsListening(true);
    recognitionRef.current.start();
  };

  const handleRun = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code })
      });
      const data = await response.json();
      const result = data.stdout || data.stderr || data.error;
      setOutput(result);
    } catch (error) {
      setOutput("Failed to run code: " + error.message);
    }
  };

  const handleAskAI = async () => {
    if (!promptInput.trim()) return;

    const userCode = editorRef.current?.getValue() || "";
    const prompt = promptInput;

    setChatLog(prev => [...prev, { role: "user", content: prompt }]);
    setPromptInput("");

    try {
      const res = await fetch(`${BACKEND_URL}/ask-ai`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, user_code: userCode })
      });

      const data = await res.json();
      const aiReply = data.response || "⚠️ No response from AI.";
      setChatLog(prev => [...prev, { role: "assistant", content: aiReply }]);
    } catch (err) {
      const failMsg = "⚠️ AI request failed: " + err.message;
      setChatLog(prev => [...prev, { role: "assistant", content: failMsg }]);
    }
  };

  const copyToEditor = (content) => {
    const existing = editorRef.current?.getValue() || "";
    editorRef.current?.setValue(existing + "\n\n# AI Suggestion:\n" + content);
  };

  return (
    <div className="app-container">
      <div className="top-section">
        <div className="left-panel">
          <Editor
            height="100%"
            language="python"
            theme="vs-dark"
            value={code}
            onChange={(val) => setCode(val)}
            onMount={(editor) => (editorRef.current = editor)}
          />
          <div className="button-group">
            <button onClick={handleRun}>Run</button>
          </div>
        </div>

        <div className="right-panel">
          <h2>AI Assistant</h2>
          <div className="chat-box">
            {chatLog.map((entry, index) => (
              <div key={index} className="ai-message-box">
                <p><strong>{entry.role === "user" ? "You" : "AI"}:</strong></p>
                <pre>{entry.content}</pre>
                {entry.role === "assistant" && (
                  <button className="copy-button" onClick={() => copyToEditor(entry.content)}>
                    Copy to Editor
                  </button>
                )}
              </div>
            ))}
          </div>
          <div className="chat-input">
            <input
              type="text"
              placeholder="Ask something..."
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAskAI()}
            />
            <button
              className="mic-button"
              onClick={handleMicClick}
              style={{ marginLeft: '8px', background: isListening ? '#e0e0e0' : undefined }}
              title="Speak"
            >
              {isListening ? '🎤...' : '🎤'}
            </button>
            <button onClick={handleAskAI} style={{ marginLeft: '8px' }}>Send</button>
          </div>
        </div>
      </div>

      <div className="output-section">
        <h3>Output:</h3>
        <pre>{output}</pre>
      </div>
    </div>
  );
}

export default App;

