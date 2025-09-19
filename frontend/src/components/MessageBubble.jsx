import React from 'react'

export default function MessageBubble({ role, content }) {
  const isUser = role === 'user'
  return (
    <div className={`bubble ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && <div className="avatar">🤖</div>}
      <div className="bubble-content">
        <div className="text" dangerouslySetInnerHTML={{ __html: escapeToHTML(content) }}></div>
        <div className="meta">
          {isUser ? 'You' : 'Assistant'}
        </div>
      </div>
      {isUser && <div className="avatar user">🧑</div>}
    </div>
  )
}

function escapeToHTML(text) {
  // Basic newline -> <br> and code block support
  const safe = (text || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>')

  // simple markdown-ish bold
  return safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}