import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground mt-2">
          Welcome to Claude Assistant. Your AI-powered coding companion.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Stats Cards */}
        <Card>
          <CardHeader>
            <CardTitle>Total Conversations</CardTitle>
            <CardDescription>All-time conversation count</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">0</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active Projects</CardTitle>
            <CardDescription>Currently active projects</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">0</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API Calls Today</CardTitle>
            <CardDescription>Requests made today</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">0</div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
        <div className="flex gap-4">
          <Button>New Conversation</Button>
          <Button variant="outline">View Projects</Button>
          <Button variant="outline">Settings</Button>
        </div>
      </div>
    </div>
  );
}
