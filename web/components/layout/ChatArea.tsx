"use client";

import { useEffect, useRef } from "react";
import { useSessionStore } from "@/lib/stores/useSessionStore";
import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import { Message } from "@/lib/api/types";

interface ChatAreaProps {
  messages: Message[];
  isLoading?: boolean;
  streamingContent?: string;
  sdkSessionId?: string;
}

function parseMessageData(data: string): { role: string; content: string } {
  try {
    const parsed = JSON.parse(data);
    return {
      role: parsed.role || "assistant",
      content: typeof parsed.content === "string" 
        ? parsed.content 
        : JSON.stringify(parsed.content),
    };
  } catch {
    return { role: "assistant", content: data };
  }
}

export function ChatArea({ messages, isLoading, streamingContent, sdkSessionId }: ChatAreaProps) {
  const { selectedSession } = useSessionStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  if (!selectedSession) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center">
          <p className="text-lg font-medium">No session selected</p>
          <p className="text-sm mt-1">Select a session to view messages</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center">
          <div className="animate-spin size-8 border-2 border-muted-foreground border-t-foreground rounded-full mx-auto" />
          <p className="text-sm mt-3">Loading messages...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 gap-4">
      {sdkSessionId && (
        <div className="flex items-center justify-between text-xs text-muted-foreground border-b border-border pb-2">
          <span>SDK Session ID</span>
          <span className="font-mono text-[10px]">{sdkSessionId}</span>
        </div>
      )}
      {messages.length === 0 && !streamingContent ? (
        <div className="flex h-full items-center justify-center text-muted-foreground">
          <div className="text-center">
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm mt-1">Start a conversation</p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => {
            const { role, content } = parseMessageData(message.data);
            const isUser = role === "user";

            return (
              <div
                key={message.message_unique_id}
                className={cn(
                  "flex gap-3",
                  isUser ? "flex-row-reverse" : "flex-row"
                )}
              >
                <div
                  className={cn(
                    "flex size-8 shrink-0 items-center justify-center rounded-lg",
                    isUser
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {isUser ? (
                    <User className="size-4" />
                  ) : (
                    <Bot className="size-4" />
                  )}
                </div>

                <div
                  className={cn(
                    "flex-1 max-w-[80%] rounded-xl px-4 py-3",
                    isUser
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap break-words">
                    {content}
                  </p>
                  <p
                    className={cn(
                      "text-xs mt-2",
                      isUser
                        ? "text-primary-foreground/60"
                        : "text-muted-foreground"
                    )}
                  >
                    {new Date(message.gmt_create * 1000).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            );
          })}

          {streamingContent && (
            <div className="flex gap-3 flex-row">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <Bot className="size-4" />
              </div>

              <div className="flex-1 max-w-[80%] rounded-xl px-4 py-3 bg-muted text-foreground">
                <p className="text-sm whitespace-pre-wrap break-words">
                  {streamingContent}
                </p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
}
