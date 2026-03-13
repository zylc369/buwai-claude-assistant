/**
 * Server-Sent Events (SSE) client for real-time updates
 */

type EventHandler = (event: any) => void;

export class SSEClient {
  private eventSource: EventSource | null = null;
  private handlers: Map<string, EventHandler[]> = new Map();
  
  connect(url: string = 'http://localhost:8000/events/stream') {
    if (this.eventSource) {
      this.disconnect();
    }
    
    this.eventSource = new EventSource(url);
    
    this.eventSource.onopen = () => {
      console.log('SSE connection opened');
    };
    
    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit(data.type, data);
      } catch (error) {
        console.error('Failed to parse SSE event:', error);
      }
    };
    
    this.eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      // Auto-reconnect on error
      setTimeout(() => this.connect(url), 5000);
    };
  }
  
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
  
  on(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }
  
  off(eventType: string, handler: EventHandler) {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }
  
  private emit(eventType: string, data: any) {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }
}

// Singleton instance
let sseClient: SSEClient | null = null;

export function getSSEClient(): SSEClient {
  if (!sseClient) {
    sseClient = new SSEClient();
  }
  return sseClient;
}
