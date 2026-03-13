"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useWorkspaceStore } from "@/lib/stores/useWorkspaceStore";
import { useSessionStore } from "@/lib/stores/useSessionStore";
import { ChatArea } from "./ChatArea";
import { InputArea } from "../InputArea";
import { apiClient } from "@/lib/api/client";
import { FolderOpen, Radio, Wifi } from "lucide-react";
import { cn } from "@/lib/utils";
import { Message } from "@/lib/api/types";

const POLLING_INTERVAL_MS = 2000;
const STORAGE_KEY_MODE = "buwai-chat-mode";

type ChatMode = "streaming" | "polling";

export function ChatInterface() {
  const { selectedWorkspace } = useWorkspaceStore();
  const { selectedSession } = useSessionStore();
  const [streamingContent, setStreamingContent] = useState<string>("");
  const [mode, setMode] = useState<ChatMode>("polling");
  const [messages, setMessages] = useState<Message[]>([]);
  const [lastMessageId, setLastMessageId] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(STORAGE_KEY_MODE);
    if (stored === "streaming" || stored === "polling") {
      setMode(stored);
    }
  }, []);

  const handleModeChange = (newMode: ChatMode) => {
    setMode(newMode);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY_MODE, newMode);
    }
  };

  const handleStreamingContent = useCallback((content: string) => {
    setStreamingContent(content);
  }, []);

  const handleStreamEnd = useCallback(() => {
    setStreamingContent("");
  }, []);

  const loadInitialMessages = useCallback(async (sessionUniqueId: string) => {
    if (!sessionUniqueId) return;
    
    setIsLoading(true);
    try {
      const allMessages = await apiClient.getMessages({ 
        session_unique_id: sessionUniqueId 
      });
      setMessages(allMessages);
      if (allMessages.length > 0) {
        const maxId = Math.max(...allMessages.map(m => m.id));
        setLastMessageId(maxId);
      } else {
        setLastMessageId(0);
      }
    } catch (error) {
      console.error("Failed to load messages:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchIncrementalMessages = useCallback(async (sessionUniqueId: string, afterId: number) => {
    if (!sessionUniqueId) return;
    
    try {
      const newMessages = await apiClient.getMessages({ 
        session_unique_id: sessionUniqueId,
        last_message_id: afterId
      });
      
      if (newMessages.length > 0) {
        setMessages(prev => [...prev, ...newMessages]);
        const maxId = Math.max(...newMessages.map(m => m.id));
        setLastMessageId(maxId);
      }
    } catch (error) {
      console.error("Failed to fetch incremental messages:", error);
    }
  }, []);

  useEffect(() => {
    if (!selectedSession?.session_unique_id) {
      setMessages([]);
      setLastMessageId(0);
      return;
    }

    loadInitialMessages(selectedSession.session_unique_id);
  }, [selectedSession?.session_unique_id, loadInitialMessages]);

  useEffect(() => {
    if (mode !== "polling" || !selectedSession?.session_unique_id) {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      return;
    }

    pollingIntervalRef.current = setInterval(() => {
      fetchIncrementalMessages(selectedSession.session_unique_id, lastMessageId);
    }, POLLING_INTERVAL_MS);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [mode, selectedSession?.session_unique_id, lastMessageId, fetchIncrementalMessages]);

  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  if (!selectedWorkspace) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
        <div className="flex flex-col items-center gap-4">
          <div className="flex size-16 items-center justify-center rounded-2xl bg-muted">
            <FolderOpen className="size-8 text-muted-foreground/60" />
          </div>
          <div className="text-center">
            <p className="text-lg font-medium">Select workspace to start</p>
            <p className="text-sm mt-1 text-muted-foreground/80">
              Choose a workspace from the sidebar to begin chatting
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-end gap-2 px-4 py-2 border-b border-border bg-muted/30">
        <span className="text-xs text-muted-foreground mr-2">Mode:</span>
        <button
          onClick={() => handleModeChange("polling")}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
            mode === "polling"
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
          title="Polling mode (2s interval)"
        >
          <Radio className="size-3" />
          Polling
        </button>
        <button
          onClick={() => handleModeChange("streaming")}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
            mode === "streaming"
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
          title="Streaming mode (SSE)"
        >
          <Wifi className="size-3" />
          Streaming
        </button>
      </div>

      <ChatArea 
        messages={messages} 
        isLoading={isLoading}
        streamingContent={streamingContent} 
      />
      <InputArea
        onStreamingContent={mode === "streaming" ? handleStreamingContent : undefined}
        onStreamEnd={handleStreamEnd}
      />
    </div>
  );
}
