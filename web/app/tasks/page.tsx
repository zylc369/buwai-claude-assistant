'use client';

import { useState, useEffect } from 'react';
import { useTasks, useCreateTask, useUpdateTask, useDeleteTask } from '@/hooks/useTasks';
import { useProjects } from '@/hooks/useProjects';
import { useUsers } from '@/hooks/useUsers';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Task, CreateTaskRequest } from '@/lib/api/types';
import { getSSEClient } from '@/lib/api/sse';

interface TaskFilter {
  projectId?: number;
  status?: string;
}

export default function TasksPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [filter, setFilter] = useState<TaskFilter>({});
  const [formData, setFormData] = useState<CreateTaskRequest>({
    title: '',
    description: '',
    project_id: 1,
    assignee_id: undefined,
    status: 'pending',
    priority: 'normal',
  });

  const { data: tasks, isLoading, error } = useTasks(filter);
  const { data: projects } = useProjects();
  const { data: users } = useUsers();
  const createTask = useCreateTask();
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();

  // Subscribe to SSE for real-time updates
  useEffect(() => {
    const sseClient = getSSEClient();
    sseClient.connect();
    
    const handleTaskUpdate = (event: any) => {
      console.log('Task updated:', event);
      // React Query will automatically refetch
    };
    
    sseClient.on('task_update', handleTaskUpdate);
    
    return () => {
      sseClient.off('task_update', handleTaskUpdate);
      sseClient.disconnect();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (editingTask) {
      await updateTask.mutateAsync({
        id: editingTask.id,
        data: {
          title: formData.title,
          description: formData.description,
          assignee_id: formData.assignee_id,
          status: formData.status,
          priority: formData.priority,
        },
      });
    } else {
      await createTask.mutateAsync(formData);
    }
    
    resetForm();
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    setFormData({
      title: task.title,
      description: task.description || '',
      project_id: task.project_id,
      assignee_id: task.assignee_id || undefined,
      status: task.status,
      priority: task.priority,
    });
    setIsCreateModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this task?')) {
      await deleteTask.mutateAsync(id);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      project_id: 1,
      assignee_id: undefined,
      status: 'pending',
      priority: 'normal',
    });
    setEditingTask(null);
    setIsCreateModalOpen(false);
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-700',
      in_progress: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      cancelled: 'bg-gray-100 text-gray-700',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-700';
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      low: 'text-gray-600',
      normal: 'text-blue-600',
      high: 'text-red-600',
    };
    return colors[priority as keyof typeof colors] || 'text-gray-600';
  };

  if (isLoading) return <div className="p-8">Loading...</div>;
  if (error) return <div className="p-8 text-red-500">Error: {error.message}</div>;

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Tasks</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>Create Task</Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          className="px-4 py-2 border rounded"
          value={filter.projectId || ''}
          onChange={(e) => setFilter({ ...filter, projectId: e.target.value ? Number(e.target.value) : undefined })}
        >
          <option value="">All Projects</option>
          {projects?.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        <select
          className="px-4 py-2 border rounded"
          value={filter.status || ''}
          onChange={(e) => setFilter({ ...filter, status: e.target.value ? e.target.value : undefined })}
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Task List */}
      <div className="space-y-4">
        {tasks?.map((task) => (
          <Card key={task.id}>
            <CardContent className="pt-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">{task.title}</h3>
                  {task.description && (
                    <p className="text-gray-600 mt-1">{task.description}</p>
                  )}
                  <div className="flex gap-2 mt-2">
                    <span className={`text-xs px-2 py-1 rounded ${getStatusColor(task.status)}`}>
                      {task.status}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded ${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                    {task.due_date && (
                      <span className="text-xs text-gray-500">
                        Due: {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => handleEdit(task)}>
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDelete(task.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create/Edit Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>{editingTask ? 'Edit Task' : 'Create Task'}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Title</label>
                  <Input
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Description</label>
                  <Input
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Project</label>
                  <select
                    className="w-full px-3 py-2 border rounded"
                    value={formData.project_id}
                    onChange={(e) => setFormData({ ...formData, project_id: Number(e.target.value) })}
                  >
                    {projects?.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Assignee</label>
                  <select
                    className="w-full px-3 py-2 border rounded"
                    value={formData.assignee_id || ''}
                    onChange={(e) => setFormData({ ...formData, assignee_id: e.target.value ? Number(e.target.value) : undefined })}
                  >
                    <option value="">Unassigned</option>
                    {users?.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.username}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Status</label>
                  <select
                    className="w-full px-3 py-2 border rounded"
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                  >
                    <option value="pending">Pending</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Priority</label>
                  <select
                    className="w-full px-3 py-2 border rounded"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">
                    {editingTask ? 'Update' : 'Create'}
                  </Button>
                  <Button type="button" variant="outline" onClick={resetForm} className="flex-1">
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
