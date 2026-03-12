"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function TopBar() {
  return (
    <header className="h-16 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-full items-center justify-between px-6">
        {/* Logo/Brand */}
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold tracking-tight">
            <span className="bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent">
              Claude Assistant
            </span>
          </h1>
        </div>

        {/* Search */}
        <div className="flex-1 max-w-md mx-8">
          <Input
            type="search"
            placeholder="Search..."
            className="w-full bg-muted/50 border-muted-foreground/20"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm">
            Settings
          </Button>
          <Button variant="outline" size="sm">
            Profile
          </Button>
        </div>
      </div>
    </header>
  );
}
