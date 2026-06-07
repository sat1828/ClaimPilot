type MessageHandler = (data: unknown) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private adjusterId: string;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private url: string;

  constructor(adjusterId: string = "default-adjuster") {
    this.adjusterId = adjusterId;
    this.url = `ws://localhost:8000/ws/adjuster/${adjusterId}`;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log(`[WS] Connected as adjuster ${this.adjusterId}`);
        this.emit("connected", null);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type || "message", data);
        } catch {
          this.emit("raw", event.data);
        }
      };

      this.ws.onclose = () => {
        console.log("[WS] Disconnected");
        this.emit("disconnected", null);
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.error("[WS] Error:", err);
        this.emit("error", err);
      };
    } catch (err) {
      console.error("[WS] Connection failed:", err);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 5000);
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  send(type: string, payload: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...payload }));
    }
  }

  on(event: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)?.delete(handler);
  }

  private emit(event: string, data: unknown): void {
    this.handlers.get(event)?.forEach((handler) => handler(data));
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
export default WebSocketClient;
