import { useState } from 'react'
import type { ResumeMaterial, ResumeState } from '@/entities/resume'
import { useResumeChat } from '../model'

interface Props {
  state: ResumeState
  materials: ResumeMaterial[]
  onState: (s: ResumeState) => void
}

// AI 수정 = 버튼 하나. 누르면 말풍선(팝오버)이 열려 명령을 입력·적용한다.
// 지속되는 채팅 로그 대신, 마지막 응답만 말풍선 안에 보여준다.
export function ChatBubble({ state, materials, onState }: Props) {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [reply, setReply] = useState('')
  const chat = useResumeChat((s, r) => {
    onState(s)
    setReply(r)
    setInput('')
  })

  const send = () => {
    const message = input.trim()
    if (!message) return
    chat.mutate({ state, materials, message })
  }

  return (
    <div className="resume-chat">
      {open && (
        <div className="resume-chat-bubble">
          {chat.isPending ? (
            <div className="resume-chat-reply">…수정 중</div>
          ) : (
            reply && <div className="resume-chat-reply">{reply}</div>
          )}
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
            autoFocus
          />
          <div className="resume-chat-actions">
            <button onClick={() => setOpen(false)}>닫기</button>
            <button onClick={send} disabled={chat.isPending}>
              보내기
            </button>
          </div>
        </div>
      )}
      <button className="resume-chat-trigger" onClick={() => setOpen((o) => !o)}>
        ✨ AI로 수정
      </button>
    </div>
  )
}
