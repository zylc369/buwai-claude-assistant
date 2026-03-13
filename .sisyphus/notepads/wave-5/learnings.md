
## Sidebar Component (Task 21) - 2026-03-13

### Design System Patterns
- **Color tokens**: Always use semantic tokens (bg-background, text-foreground, bg-muted, border-border, text-muted-foreground, bg-accent)
- **Typography**: text-xs for labels, text-sm for content, text-base for titles, font-semibold for headings
- **Spacing**: Follow Tailwind scale (gap-2, p-3, space-y-1, max-h-48)
- **Components**: Reuse existing Button (variants: ghost, outline), Input, Dialog from Base UI
- **Patterns**: "use client", cn() utility, data-slot attributes

### Component Architecture
- Two-file pattern: Main component in `web/components/Sidebar.tsx`, wrapper in `web/components/layout/Sidebar.tsx`
- Stores only manage selected items (selectedWorkspace, selectedSession)
- Lists come from API hooks (not implemented yet - using mock data)
- Zustand stores use persist middleware for localStorage

### Implementation Details
- Workspace list: max-h-48 overflow-y-auto for scrollable section
- Session list: flex-1 overflow-y-auto for flexible scrolling
- Time formatting: Simple relative time (Just now, Xh ago, Xd ago)
- Dialog: Base UI Dialog with backdrop, animations using Tailwind animate-in/out
- Selection state: Use bg-accent/50 for selected items

### TODO Comments
- Necessary to document future API integration points
- Placeholder data with clear comment explaining it's temporary
- Commented-out hook usage examples to guide future implementation

### File Structure
```
web/components/Sidebar.tsx (main component)
web/components/layout/Sidebar.tsx (wrapper)
web/lib/stores/useWorkspaceStore.ts (selected workspace state)
web/lib/stores/useSessionStore.ts (selected session state)
web/lib/store.ts (barrel export)
```

## InputArea Component (Task 22)

### Design Patterns Used
- Tailwind CSS with CSS variables for theming (--background, --foreground, --border, --muted, etc.)
- `cn()` utility for conditional class composition
- Base-UI Button primitive with class-variance-authority variants
- "use client" directive for client-side interactivity

### Keyboard Shortcuts Implementation
- `Enter` sends message (preventDefault on non-modified Enter)
- `Shift+Enter` allows newline (default behavior)
- `Cmd/Ctrl+Enter` allows newline (default behavior)

### Streaming Integration
- Uses `apiClient.streamAIResponse()` async generator
- Callbacks: `onStreamingContent` for accumulated content, `onStreamEnd` for completion
- Loading state with Loader2 spinner icon

### Auto-resize Textarea
- Dynamic height adjustment up to 200px max
- Uses `scrollHeight` for natural text flow
