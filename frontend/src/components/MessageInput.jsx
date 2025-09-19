import React, { useState } from 'react'

export default function MessageInput({ onSend, disabled }) {
  const [value, setValue] = useState('')

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    if (!value.trim() || disabled) return
    onSend(value.trim())
    setValue('')
  }

  return (
    <div className="input-wrapper">
      <textarea
        className="input"
        placeholder="Yahan type karein... (e.g. mujhe karachi se lahore jana hai kal)"
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
      />
      <button className="btn send" onClick={submit} disabled={disabled || !value.trim()}>
        {disabled ? '...' : 'Send'}
      </button>
    </div>
  )
}