import React, { useEffect, useRef, useState } from 'react'
import MessageBubble from './components/MessageBubble.jsx'
import MessageInput from './components/MessageInput.jsx'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: crypto.randomUUID(),
      role: 'assistant',
      content:
        'Assalam-o-Alaikum! 👋 Main aapki train booking mein madad karunga. Naya chat start ho gaya hai.'
    }
  ])
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(localStorage.getItem('pakrail_session_id') || '')
  const bottomRef = useRef(null)

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  async function sendMessage(text) {
    if (!text.trim()) return

    // push user msg
    const userMsg = { id: crypto.randomUUID(), role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, sessionId: sessionId || null })
      })
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data = await res.json()
      if (data?.sessionId && data.sessionId !== sessionId) {
        setSessionId(data.sessionId)
        localStorage.setItem('pakrail_session_id', data.sessionId)
      }
      const assistantMsg = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.reply || '...'
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      const errMsg = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '😔 Server issue aa gaya hai. Thodi der baad try kijiye.'
      }
      setMessages(prev => [...prev, errMsg])
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleNewChat() {
    try {
      const sid = localStorage.getItem('pakrail_session_id')
      if (sid) {
        await fetch(`${API_BASE}/api/reset`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sessionId: sid })
        })
      }
    } catch (e) {
      // ignore
    }
    localStorage.removeItem('pakrail_session_id')
    setSessionId('')
    setMessages([
      {
        id: crypto.randomUUID(),
        role: 'assistant',
        content:
          'Naya chat start ho gaya hai. Aap apna sawal likhein ya just keh dijiye: "mujhe lahore se karachi jana hai"'
      }
    ])
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="logo">🚂</span>
          <div className="brand-text">
            <div className="title">PakRail AI</div>
            <div className="subtitle">Pakistan Railway Booking Assistant</div>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn ghost" onClick={handleNewChat}>+ New Chat</button>
          <a className="btn primary" href="https://pakrail.gov.pk" target="_blank" rel="noreferrer">PakRail</a>
        </div>
      </header>

      <main className="chat-container">
        {messages.map(m => (
          <MessageBubble key={m.id} role={m.role} content={m.content} />
        ))}

        {loading && (
          <div className="bubble assistant">
            <div className="typing">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={bottomRef}></div>
      </main>

      <footer className="chat-input">
        <MessageInput onSend={sendMessage} disabled={loading} />
        <div className="hint">
          Tip: Enter se send, Shift+Enter se new line. New chat ke liye top right button use karein.
        </div>
      </footer>
    </div>
  )
}