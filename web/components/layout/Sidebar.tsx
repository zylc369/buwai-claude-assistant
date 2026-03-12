"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

export function Sidebar() {
  const pathname = usePathname();
  
  const isActive = (path: string) => pathname === path;
  
  return (
    <aside className="w-64 border-r border-border bg-muted/30">
      <div className="flex flex-col h-full">
        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          <div className="space-y-1">
            <Link href="/">
              <Button
                variant={isActive("/") ? "default" : "ghost"}
                className="w-full justify-start"
              >
                Dashboard
              </Button>
            </Link>
            <Link href="/users">
              <Button
                variant={isActive("/users") ? "default" : "ghost"}
                className="w-full justify-start"
              >
                Users
              </Button>
            </Link>
            <Link href="/projects">
              <Button
                variant={isActive("/projects") ? "default" : "ghost"}
                className="w-full justify-start"
              >
                Projects
              </Button>
            </Link>
            <Link href="/tasks">
              <Button
                variant={isActive("/tasks") ? "default" : "ghost"}
                className="w-full justify-start"
              >
                Tasks
              </Button>
            </Link>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <p className="text-xs text-muted-foreground">
            © 2026 Claude Assistant
          </p>
        </div>
      </div>
    </aside>
  );
}
