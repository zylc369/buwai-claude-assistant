"use client";

import { useState, useEffect } from "react";
import { Dialog } from "@base-ui/react";
import { Plus, MessageSquare, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useWorkspaceStore, useSessionStore, useProjectStore } from "@/lib/store";
import { useWorkspaces, useCreateWorkspace } from "@/hooks/useWorkspaces";
import { useSessions } from "@/hooks/useSessions";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const [isCreateWorkspaceDialogOpen, setIsCreateWorkspaceDialogOpen] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [newWorkspaceDirectory, setNewWorkspaceDirectory] = useState("");
  const [newWorkspaceBranch, setNewWorkspaceBranch] = useState("");

  const { selectedWorkspace, setSelectedWorkspace } = useWorkspaceStore();
  const { selectedSession, setSelectedSession, isNewSession, createNewSession } = useSessionStore();
  const { selectedProject } = useProjectStore();

  const { data: workspaces = [], isLoading: workspacesLoading } = useWorkspaces(selectedProject?.project_unique_id);
  const { data: sessions = [], isLoading: sessionsLoading } = useSessions({
    project_unique_id: selectedProject?.project_unique_id || '',
    workspace_unique_id: selectedWorkspace?.workspace_unique_id || '',
  });
  const createWorkspace = useCreateWorkspace();

  const sortedSessions = [...sessions].sort((a, b) => b.gmt_create - a.gmt_create);

  // Auto-select last session when workspace switches (需求 3.3)
  useEffect(() => {
    if (selectedWorkspace && sortedSessions.length > 0 && !isNewSession) {
      if (!selectedSession || selectedSession.workspace_unique_id !== selectedWorkspace.workspace_unique_id) {
        setSelectedSession(sortedSessions[0]);
      }
    }
  }, [selectedWorkspace, sortedSessions, isNewSession, setSelectedSession, selectedSession]);

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName.trim() || !newWorkspaceDirectory.trim() || !selectedProject) return;

    try {
      await createWorkspace.mutateAsync({
        workspace_unique_id: crypto.randomUUID(),
        project_unique_id: selectedProject.project_unique_id,
        branch: newWorkspaceBranch.trim() || undefined,
        directory: newWorkspaceDirectory.trim(),
      });
      setIsCreateWorkspaceDialogOpen(false);
      setNewWorkspaceName("");
      setNewWorkspaceDirectory("");
      setNewWorkspaceBranch("");
    } catch (error) {
      console.error("Failed to create workspace:", error);
    }
  };

  const handleCreateSession = () => {
    if (!selectedWorkspace || !selectedProject) return;
    createNewSession(selectedProject, selectedWorkspace);
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
        <div className="px-3 py-2 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Workspaces
          </h3>
          {selectedProject && (
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => setIsCreateWorkspaceDialogOpen(true)}
              className="h-5 w-5"
            >
              <Plus className="size-3" />
            </Button>
          )}
        </div>
        <div className="max-h-48 overflow-y-auto px-2 pb-2 space-y-1">
          {!selectedProject ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Select a project first
            </div>
          ) : workspacesLoading ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Loading...
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
                title={`projectsRoot/${selectedProject?.directory}/${workspace.directory}/`}
                className={cn(
                  "w-full flex items-center gap-2 rounded-md px-3 py-2 text-sm text-left",
                  "hover:bg-accent hover:text-accent-foreground",
                  "focus:bg-accent focus:text-accent-foreground outline-none",
                  selectedWorkspace?.id === workspace.id && "bg-accent/50"
                )}
              >
                <FolderOpen className="size-4 shrink-0 text-muted-foreground" />
                <span className="truncate">{workspace.directory}</span>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="border-b border-border">
        <div className="px-3 py-2 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            AI Resources
          </h3>
          <a
            href="/ai-resources"
            className="text-sm hover:underline text-muted-foreground hover:text-accent-foreground"
          >
            Manage
          </a>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0">
        <div className="px-3 py-2 flex items-center justify-between border-b border-border">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Sessions
          </h3>
          {selectedProject && selectedWorkspace && (
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={handleCreateSession}
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
          ) : sessionsLoading ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Loading...
            </div>
          ) : (
            <>
              {isNewSession && selectedSession && (
                <button
                  className={cn(
                    "w-full flex items-start gap-2 rounded-md px-3 py-2 text-left",
                    "bg-accent/50 border border-primary/20",
                    "focus:bg-accent focus:text-accent-foreground outline-none"
                  )}
                >
                  <MessageSquare className="size-4 shrink-0 mt-0.5 text-primary" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm truncate flex items-center gap-1.5">
                      <span>{selectedSession.title || 'New Chat'}</span>
                      <span className="text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">New</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Just now
                    </div>
                  </div>
                </button>
              )}
              
              {sortedSessions.length === 0 && !isNewSession ? (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  No sessions yet
                </div>
              ) : (
                sortedSessions.map((session) => (
                  <button
                    key={session.id}
                    onClick={() => setSelectedSession(session)}
                    className={cn(
                      "w-full flex items-start gap-2 rounded-md px-3 py-2 text-left",
                      "hover:bg-accent hover:text-accent-foreground",
                      "focus:bg-accent focus:text-accent-foreground outline-none",
                      selectedSession?.id === session.id && !isNewSession && "bg-accent/50"
                    )}
                  >
                    <MessageSquare className="size-4 shrink-0 mt-0.5 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm truncate">{session.title || session.session_unique_id}</div>
                      <div className="text-xs text-muted-foreground">
                        {formatTime(session.gmt_modified)}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </>
          )}
        </div>
      </div>

      <Dialog.Root open={isCreateWorkspaceDialogOpen} onOpenChange={setIsCreateWorkspaceDialogOpen}>
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
                "w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl",
                "animate-in fade-in-0 zoom-in-95",
                "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
              )}
            >
              <Dialog.Title className="text-lg font-semibold mb-4">
                New Workspace
              </Dialog.Title>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    Workspace Name
                  </label>
                  <Input
                    value={newWorkspaceName}
                    onChange={(e) => {
                      const name = e.target.value;
                      setNewWorkspaceName(name);
                      const generatedDirectory = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9_-]/g, '');
                      setNewWorkspaceDirectory(generatedDirectory);
                    }}
                    placeholder="My Feature"
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    Directory Name
                  </label>
                  <Input
                    value={newWorkspaceDirectory}
                    onChange={(e) => setNewWorkspaceDirectory(e.target.value)}
                    placeholder="my-feature"
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    Branch (optional)
                  </label>
                  <Input
                    value={newWorkspaceBranch}
                    onChange={(e) => setNewWorkspaceBranch(e.target.value)}
                    placeholder="main"
                    className="w-full"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => setIsCreateWorkspaceDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateWorkspace}
                  disabled={!newWorkspaceName.trim() || !newWorkspaceDirectory.trim() || createWorkspace.isPending}
                >
                  {createWorkspace.isPending ? "Creating..." : "Create"}
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
