"use client";

import { useState, useRef, useCallback, KeyboardEvent, useEffect } from "react";
import { useSessionStore } from "@/lib/stores/useSessionStore";
import { apiClient } from "@/lib/api/client";
import { cn } from "@/lib/utils";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface InputAreaProps {
  onStreamingContent?: (content: string) => void;
  onStreamEnd?: () => void;
  onSdkSessionId?: (sdkSessionId: string) => void;
}

export function InputArea({ onStreamingContent, onStreamEnd, onSdkSessionId }: InputAreaProps) {
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const { selectedSession } = useSessionStore();

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, [selectedSession?.session_unique_id]);

  const isDisabled = !selectedSession || isSending || !input.trim();

  const handleSubmit = useCallback(async () => {
    if (isDisabled) return;

    const prompt = input.trim();
    setInput("");
    setIsSending(true);

    abortControllerRef.current = new AbortController();

    try {
      const generator = apiClient.streamAIResponse(
        {
          prompt,
          session_unique_id: selectedSession!.session_unique_id,
          cwd: selectedSession!.directory,
          settings: "",
        },
        abortControllerRef.current.signal
      );

      let accumulatedContent = "";

      for await (const event of generator) {
        if (event.type === "chunk" && event.content) {
          const content = typeof event.content === "string" 
            ? event.content 
            : JSON.stringify(event.content);
          accumulatedContent += content;
          onStreamingContent?.(accumulatedContent);
        } else if (event.type === "done") {
          if (event.sdk_session_id) {
            onSdkSessionId?.(event.sdk_session_id);
          }
          onStreamEnd?.();
        } else if (event.type === "error") {
          console.error("Stream error:", event.message);
          onStreamEnd?.();
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        onStreamEnd?.();
      } else {
        console.error("Failed to send message:", error);
        onStreamEnd?.();
      }
    } finally {
      setIsSending(false);
      abortControllerRef.current = null;
    }
  }, [input, isDisabled, selectedSession, onStreamingContent, onStreamEnd]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !(e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (value: string) => {
    setInput(value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  return (
    <div className="border-t border-border bg-background p-4">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => handleInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedSession
                ? "Type a message... (Enter to send, ⌘/Shift+Enter for newline)"
                : "Select a session to start chatting"
            }
            disabled={!selectedSession || isSending}
            rows={1}
            className={cn(
              "w-full min-h-[40px] max-h-[200px] resize-none rounded-xl border border-input bg-transparent px-4 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50"
            )}
          />
        </div>
        <Button
          onClick={handleSubmit}
          disabled={isDisabled}
          variant="default"
          size="icon"
          className="shrink-0 rounded-xl"
          aria-label="Send message"
        >
          {isSending ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Send className="size-4" />
          )}
        </Button>
      </div>
      <div className="mt-2 text-xs text-muted-foreground text-center">
        Press <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono text-[10px]">Enter</kbd> to send,{" "}
        <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono text-[10px]">⌘/Shift+Enter</kbd> for newline
      </div>
    </div>
  );
}
