"use client";

import { useState } from "react";
import { Dialog } from "@base-ui/react";
import { Plus, MessageSquare, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useWorkspaceStore, useSessionStore, useProjectStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { Workspace, Session } from "@/lib/api/types";

// Placeholder data - will be replaced with hooks when API is ready
const mockWorkspaces: Workspace[] = [
  {
    id: 1,
    workspace_unique_id: "ws-1",
    project_unique_id: "proj-1",
    name: "Development",
    branch: "main",
    directory: "/workspace/dev",
    extra: null,
  },
  {
    id: 2,
    workspace_unique_id: "ws-2",
    project_unique_id: "proj-1",
    name: "Feature Branch",
    branch: "feature/new-ui",
    directory: "/workspace/feature",
    extra: null,
  },
];

const mockSessions: Session[] = [
  {
    id: 1,
    session_unique_id: "sess-1",
    project_unique_id: "proj-1",
    workspace_unique_id: "ws-1",
    directory: "/workspace/dev",
    title: "Initial Setup",
    time_created: Date.now() - 86400000,
    time_updated: Date.now() - 3600000,
    time_compacting: null,
    time_archived: null,
  },
  {
    id: 2,
    session_unique_id: "sess-2",
    project_unique_id: "proj-1",
    workspace_unique_id: "ws-1",
    directory: "/workspace/dev",
    title: "Bug Fixes",
    time_created: Date.now() - 172800000,
    time_updated: Date.now() - 7200000,
    time_compacting: null,
    time_archived: null,
  },
];

export function Sidebar() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState("");

  const { selectedWorkspace, setSelectedWorkspace } = useWorkspaceStore();
  const { selectedSession, setSelectedSession } = useSessionStore();
  const { selectedProject } = useProjectStore();

  // TODO: Replace with actual hooks when API is ready
  // const { data: workspaces = [] } = useWorkspaces(selectedProject?.project_unique_id);
  // const { data: sessions = [] } = useSessions(selectedProject?.project_unique_id, selectedWorkspace?.workspace_unique_id);
  // const createSession = useCreateSession();

  const workspaces = selectedProject ? mockWorkspaces : [];
  const sessions = selectedWorkspace
    ? mockSessions.filter((s) => s.workspace_unique_id === selectedWorkspace.workspace_unique_id)
    : [];

  const handleCreateSession = async () => {
    if (!newSessionTitle.trim() || !selectedWorkspace || !selectedProject) return;

    try {
      // TODO: Call create session API
      // await createSession.mutateAsync({
      //   session_unique_id: crypto.randomUUID(),
      //   project_unique_id: selectedProject.project_unique_id,
      //   workspace_unique_id: selectedWorkspace.workspace_unique_id,
      //   directory: selectedWorkspace.directory || "",
      //   title: newSessionTitle.trim(),
      // });

      console.log("Create session:", newSessionTitle);
      setIsCreateDialogOpen(false);
      setNewSessionTitle("");
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const formatTime = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (hours < 1) return "Just now";
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return new Date(timestamp).toLocaleDateString();
  };

  return (
    <aside className="w-64 border-r border-border bg-muted/30 flex flex-col h-full">
      <div className="border-b border-border">
        <div className="px-3 py-2">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Workspaces
          </h3>
        </div>
        <div className="max-h-48 overflow-y-auto px-2 pb-2 space-y-1">
          {!selectedProject ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Select a project first
            </div>
          ) : workspaces.length === 0 ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              No workspaces
            </div>
          ) : (
            workspaces.map((workspace) => (
              <button
                key={workspace.id}
                onClick={() => setSelectedWorkspace(workspace)}
                className={cn(
                  "w-full flex items-center gap-2 rounded-md px-3 py-2 text-sm text-left",
                  "hover:bg-accent hover:text-accent-foreground",
                  "focus:bg-accent focus:text-accent-foreground outline-none",
                  selectedWorkspace?.id === workspace.id && "bg-accent/50"
                )}
              >
                <FolderOpen className="size-4 shrink-0 text-muted-foreground" />
                <span className="truncate">{workspace.name || workspace.workspace_unique_id}</span>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0">
        <div className="px-3 py-2 flex items-center justify-between border-b border-border">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Sessions
          </h3>
          {selectedWorkspace && (
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => setIsCreateDialogOpen(true)}
              className="h-5 w-5"
            >
              <Plus className="size-3" />
            </Button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
          {!selectedWorkspace ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Select a workspace
            </div>
          ) : sessions.length === 0 ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              No sessions yet
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => setSelectedSession(session)}
                className={cn(
                  "w-full flex items-start gap-2 rounded-md px-3 py-2 text-left",
                  "hover:bg-accent hover:text-accent-foreground",
                  "focus:bg-accent focus:text-accent-foreground outline-none",
                  selectedSession?.id === session.id && "bg-accent/50"
                )}
              >
                <MessageSquare className="size-4 shrink-0 mt-0.5 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm truncate">{session.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {formatTime(session.time_updated)}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <Dialog.Root open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <Dialog.Portal>
          <Dialog.Backdrop
            className={cn(
              "fixed inset-0 bg-black/50 z-50",
              "animate-in fade-in-0",
              "data-[state=closed]:animate-out data-[state=closed]:fade-out-0"
            )}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <Dialog.Popup
              className={cn(
                "w-full max-w-sm rounded-xl border border-border bg-background p-6 shadow-xl",
                "animate-in fade-in-0 zoom-in-95",
                "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
              )}
            >
              <Dialog.Title className="text-base font-semibold mb-4">
                New Session
              </Dialog.Title>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    Session Title
                  </label>
                  <Input
                    value={newSessionTitle}
                    onChange={(e) => setNewSessionTitle(e.target.value)}
                    placeholder="Enter session title..."
                    className="w-full"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleCreateSession();
                      }
                    }}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateSession}
                  disabled={!newSessionTitle.trim()}
                >
                  Create
                </Button>
              </div>

              <Dialog.Close
                className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100 cursor-pointer"
              >
                <span className="sr-only">Close</span>
                ×
              </Dialog.Close>
            </Dialog.Popup>
          </div>
        </Dialog.Portal>
      </Dialog.Root>
    </aside>
  );
}
