import { useState } from 'react'
import type { ResumeMaterial, ResumeState } from '@/entities/resume'
import { useResumeChat } from '../model'

interface Msg {
  role: 'user' | 'ai'
  text: string
}
interface Props {
  state: ResumeState
  materials: ResumeMaterial[]
  onState: (s: ResumeState) => void
}

export function ChatPanel({ state, materials, onState }: Props) {
  const [log, setLog] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const chat = useResumeChat((s, reply) => {
    onState(s)
    setLog((l) => [...l, { role: 'ai', text: reply }])
  })

  const send = () => {
    const message = input.trim()
    if (!message) return
    setLog((l) => [...l, { role: 'user', text: message }])
    chat.mutate({ state, materials, message })
    setInput('')
  }

  return (
    <aside className="resume-chat">
      <div className="resume-chat-log">
        {log.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.text}
          </div>
        ))}
        {chat.isPending && <div className="msg ai">…</div>}
      </div>
      <div className="resume-chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
          placeholder="예: 경력을 성과 중심으로 다듬고 제목을 남색으로"
        />
        <button onClick={send} disabled={chat.isPending}>
          보내기
        </button>
      </div>
    </aside>
  )
}
