"use client";

import { useState } from "react";
import { Menu, Dialog } from "@base-ui/react";
import { ChevronDown, Plus, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useProjectStore } from "@/lib/stores/useProjectStore";
import { useProjects, useCreateProject } from "@/hooks/useProjects";
import { cn } from "@/lib/utils";

export function TopBar() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectWorktree, setNewProjectWorktree] = useState("");

  const { selectedProject, setSelectedProject } = useProjectStore();
  const { data: projects = [], isLoading } = useProjects();
  const createProject = useCreateProject();

  const handleSelectProject = (project: typeof selectedProject) => {
    if (project) {
      setSelectedProject(project);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim() || !newProjectWorktree.trim()) return;

    try {
      const project = await createProject.mutateAsync({
        project_unique_id: crypto.randomUUID(),
        worktree: newProjectWorktree.trim(),
        name: newProjectName.trim(),
      });
      setSelectedProject(project);
      setIsCreateDialogOpen(false);
      setNewProjectName("");
      setNewProjectWorktree("");
    } catch (error) {
      console.error("Failed to create project:", error);
    }
  };

  return (
    <header className="h-14 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-full items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="size-7 rounded-lg bg-gradient-to-br from-violet-600 to-blue-600 flex items-center justify-center">
              <span className="text-white text-sm font-bold">C</span>
            </div>
            <span className="text-base font-semibold tracking-tight text-foreground">
              Claude Assistant
            </span>
          </div>
        </div>

        <Menu.Root>
          <Menu.Trigger
            render={
              <Button
                variant="outline"
                className="min-w-[200px] justify-between"
              >
                <div className="flex items-center gap-2">
                  <FolderOpen className="size-4 text-muted-foreground" />
                  <span className="truncate">
                    {isLoading
                      ? "Loading..."
                      : selectedProject?.name || "Select Project"}
                  </span>
                </div>
                <ChevronDown className="size-4 text-muted-foreground" />
              </Button>
            }
          />

          <Menu.Portal>
            <Menu.Positioner
              sideOffset={4}
              className="z-50"
            >
              <Menu.Popup
                className={cn(
                  "min-w-[200px] rounded-lg border border-border bg-popover p-1",
                  "shadow-lg shadow-black/5",
                  "animate-in fade-in-0 zoom-in-95",
                  "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
                )}
              >
                {projects.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-muted-foreground text-center">
                    No projects available
                  </div>
                ) : (
                  projects.map((project) => (
                    <Menu.Item
                      key={project.id}
                      onClick={() => handleSelectProject(project)}
                      className={cn(
                        "flex items-center gap-2 rounded-md px-3 py-2 text-sm cursor-pointer",
                        "outline-none select-none",
                        "hover:bg-accent hover:text-accent-foreground",
                        "focus:bg-accent focus:text-accent-foreground",
                        selectedProject?.id === project.id && "bg-accent/50"
                      )}
                    >
                      <FolderOpen className="size-4" />
                      <span className="truncate">{project.name || project.project_unique_id}</span>
                    </Menu.Item>
                  ))
                )}

                <Menu.Separator className="my-1 h-px bg-border" />

                <Menu.Item
                  onClick={() => setIsCreateDialogOpen(true)}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm cursor-pointer",
                    "outline-none select-none",
                    "hover:bg-accent hover:text-accent-foreground",
                    "focus:bg-accent focus:text-accent-foreground"
                  )}
                >
                  <Plus className="size-4" />
                  <span>New Project</span>
                </Menu.Item>
              </Menu.Popup>
            </Menu.Positioner>
          </Menu.Portal>
        </Menu.Root>

        <div className="flex items-center gap-2">
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
                    "w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl",
                    "animate-in fade-in-0 zoom-in-95",
                    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
                  )}
                >
                  <Dialog.Title className="text-lg font-semibold mb-4">
                    Create New Project
                  </Dialog.Title>

                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-1.5 block">
                        Project Name
                      </label>
                      <Input
                        value={newProjectName}
                        onChange={(e) => setNewProjectName(e.target.value)}
                        placeholder="My Awesome Project"
                        className="w-full"
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-1.5 block">
                        Worktree Path
                      </label>
                      <Input
                        value={newProjectWorktree}
                        onChange={(e) => setNewProjectWorktree(e.target.value)}
                        placeholder="/path/to/project"
                        className="w-full"
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
                      onClick={handleCreateProject}
                      disabled={!newProjectName.trim() || !newProjectWorktree.trim() || createProject.isPending}
                    >
                      {createProject.isPending ? "Creating..." : "Create"}
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
        </div>
      </div>
    </header>
  );
}
