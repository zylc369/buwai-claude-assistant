"use client";

import { useState } from "react";
import { useAIResources } from "@/hooks/useAIResources";
import { useCreateAIResource } from "@/hooks/useAIResources";
import { useUpdateAIResource } from "@/hooks/useAIResources";
import { useDeleteAIResource } from "@/hooks/useAIResources";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { AIResource, AIResourceType, ContentSchema } from "@/lib/api/types";

export default function AIResourcesPage() {
  const { data: resources, isLoading } = useAIResources({ test: false });
  const createMutation = useCreateAIResource();
  const updateMutation = useUpdateAIResource();
  const deleteMutation = useDeleteAIResource();
  
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingResource, setEditingResource] = useState<AIResource | null>(null);
  const [formData, setFormData] = useState<{
    name: string;
    type: AIResourceType;
    sub_type: string;
    owner: string;
    disabled: boolean;
    content: ContentSchema;
    test: boolean;
  }>({
    name: "",
    type: "SKILL",
    sub_type: "",
    owner: "",
    disabled: false,
    content: { type: "MD", data: "" },
    test: false,
  });

  const handleCreate = async () => {
    await createMutation.mutateAsync(formData);
    setIsDialogOpen(false);
    resetForm();
  };

  const handleUpdate = async () => {
    if (editingResource) {
      await updateMutation.mutateAsync({
        resourceUniqueId: editingResource.resource_unique_id,
        data: formData,
      });
      setIsDialogOpen(false);
      resetForm();
      setEditingResource(null);
    }
  };

  const handleDelete = async (resource_unique_id: string) => {
    if (confirm("Are you sure you want to delete this resource?")) {
      await deleteMutation.mutateAsync({ resourceUniqueId: resource_unique_id });
    }
  };

  const openCreateDialog = () => {
    resetForm();
    setEditingResource(null);
    setIsDialogOpen(true);
  };

  const openEditDialog = (resource: AIResource) => {
    setFormData({
      name: resource.name,
      type: resource.type,
      sub_type: resource.sub_type,
      owner: resource.owner || "",
      disabled: resource.disabled,
      content: resource.content,
      test: resource.test,
    });
    setEditingResource(resource);
    setIsDialogOpen(true);
  };

  const resetForm = () => {
    setFormData({
      name: "",
      type: "SKILL" as const,
      sub_type: "",
      owner: "",
      disabled: false,
      content: { type: "MD" as const, data: "" },
      test: false,
    });
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">AI Resources</h1>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={openCreateDialog}>Create Resource</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>{editingResource ? "Edit Resource" : "Create Resource"}</DialogTitle>
              <DialogDescription>
                {editingResource ? "Update AI resource" : "Create new AI resource"}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Resource name"
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Type</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2"
                >
                  <option value="SKILL">Skill</option>
                  <option value="COMMAND">Command</option>
                  <option value="SYSTEM_PROMPT">System Prompt</option>
                </select>
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Sub Type</label>
                <Input
                  value={formData.sub_type}
                  onChange={(e) => setFormData({ ...formData, sub_type: e.target.value })}
                  placeholder="Sub type (optional)"
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Owner</label>
                <Input
                  value={formData.owner}
                  onChange={(e) => setFormData({ ...formData, owner: e.target.value })}
                  placeholder="Owner (empty for global)"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="disabled"
                  checked={formData.disabled}
                  onChange={(e) => setFormData({ ...formData, disabled: e.target.checked })}
                  className="h-4 w-4"
                />
                <label htmlFor="disabled" className="text-sm font-medium">
                  Disabled
                </label>
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Content Type</label>
                <select
                  value={formData.content.type}
                  onChange={(e) => setFormData({ ...formData, content: { ...formData.content, type: e.target.value as any } })}
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2"
                >
                  <option value="MD">Markdown</option>
                  <option value="SHELL">Shell</option>
                </select>
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Content Data</label>
                <textarea
                  value={formData.content.data}
                  onChange={(e) => setFormData({ ...formData, content: { ...formData.content, data: e.target.value } })}
                  placeholder="Resource content"
                  rows={10}
                  className="flex min-h-[200px] w-full rounded-md border border-input bg-transparent px-3 py-2"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                onClick={editingResource ? handleUpdate : handleCreate}
                disabled={isLoading}
              >
                {editingResource ? "Update" : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="text-center">Loading...</div>
      ) : resources && resources.length > 0 ? (
        <div className="grid gap-4">
          {resources.map((resource) => (
            <div key={resource.resource_unique_id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-semibold">{resource.name}</h3>
                <span className="text-sm px-2 py-1 rounded">
                  {resource.type}
                </span>
              </div>
              <div className="space-y-2 text-sm">
                <p><strong>Sub Type:</strong> {resource.sub_type || "-"}</p>
                <p><strong>Owner:</strong> {resource.owner || "Global"}</p>
                <p><strong>Disabled:</strong> {resource.disabled ? "Yes" : "No"}</p>
                <p><strong>Content:</strong></p>
                <pre className="bg-gray-100 p-2 rounded mt-2 overflow-x-auto">
                  {resource.content.data.substring(0, 200)}
                  {resource.content.data.length > 200 && "..."}
                </pre>
              </div>
              <div className="flex justify-end gap-2 mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => openEditDialog(resource)}
                >
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(resource.resource_unique_id)}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center text-gray-500">
          No resources found. Click "Create Resource" to add one.
        </div>
      )}
    </div>
  );
}
