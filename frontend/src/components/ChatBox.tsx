import { useEffect, useRef } from "react";
import type { Message } from "../types";

interface Props {
  messages: Message[];
}

function ChatBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div
      className={`bubble-enter flex mb-md ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[70%] px-md py-sm leading-relaxed font-ui text-[16px] ${
          isUser
            ? "bg-fog text-ink rounded-bl-bubble rounded-tl-bubble rounded-br-bubble-sm rounded-tr-bubble-sm ml-auto"
            : "bg-white text-ink rounded-br-bubble rounded-tr-bubble rounded-bl-bubble-sm rounded-tl-bubble-sm"
        }`}
        style={
          isUser
            ? undefined
            : {
                boxShadow:
                  "0 1px 3px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.03)",
              }
        }
      >
        {msg.content}
      </div>
    </div>
  );
}

export default function ChatBox({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-lg py-md">
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-mute font-ui text-[15px] leading-relaxed gap-sm">
          <span
            className="text-[32px]"
            style={{ filter: "grayscale(0.3) opacity(0.6)" }}
          >
            晚上好
          </span>
          <span>我是 Samantha，今天过得怎么样？</span>
        </div>
      )}
      {messages.map((msg) => (
        <ChatBubble key={msg.id} msg={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
