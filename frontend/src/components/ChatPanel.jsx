import React, { useRef, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendChatMessage, addUserChatMessage } from "../redux/interactionSlice";

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, isSending } = useSelector((s) => s.interaction.chat);
  const [draft, setDraft] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, isSending]);

  const handleSend = () => {
    const text = draft.trim();
    if (!text || isSending) return;
    dispatch(addUserChatMessage(text));
    dispatch(sendChatMessage(text));
    setDraft("");
  };

  return (
    <div className="panel chat-panel">
      <div className="chat-panel__header">
        <span className="dot" />
        <strong>AI Assistant</strong>
      </div>
      <p className="chat-panel__subtitle">Log interaction via chat</p>

      <div className="chat-messages" ref={scrollRef}>
        {messages.map((m, idx) => (
          <div key={idx} className={`chat-bubble ${m.role}`}>
            {m.text}
          </div>
        ))}
        {isSending && <div className="chat-bubble assistant">Thinking…</div>}
      </div>

      <div className="chat-input-row">
        <input
          type="text"
          placeholder="Describe interaction..."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button className="btn btn-primary" onClick={handleSend} disabled={isSending}>
          Log
        </button>
      </div>
    </div>
  );
}