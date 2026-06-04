/** IPC bridge — communicates with the Python backend via stdin/stdout or Tauri commands.

The pattern:
- Tauri app spawns the Python backend as a sidecar process
- IPC messages are JSON over stdin/stdout
- The frontend sends commands and receives responses
- When Python backend isn't available, falls back to mock data
*/

import type { MashupResult, MoodHistoryEntry, UserPreferences } from "../types";

const BACKEND_PORT_KEY = "cmw_backend_port";

class IPCBridge {
  private port: number | null = null;
  private ws: WebSocket | null = null;
  private mockMode = true;

  constructor() {
    const stored = localStorage.getItem(BACKEND_PORT_KEY);
    if (stored) {
      this.port = parseInt(stored, 10);
      this.mockMode = false;
    }
  }

  /** Connect to the Python backend WebSocket server. */
  async connect(port?: number): Promise<void> {
    if (port) {
      this.port = port;
      localStorage.setItem(BACKEND_PORT_KEY, String(port));
      this.mockMode = false;
    }

    if (!this.port) {
      console.log("[IPC] No backend port configured — running in mock mode");
      return;
    }

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`ws://localhost:${this.port}`);
        this.ws.onopen = () => {
          console.log(`[IPC] Connected to backend on port ${this.port}`);
          this.mockMode = false;
          resolve();
        };
        this.ws.onerror = (err) => {
          console.warn("[IPC] WebSocket error — falling back to mock mode", err);
          this.mockMode = true;
          resolve(); // resolve anyway, mock mode works
        };
        this.ws.onclose = () => {
          console.log("[IPC] Backend disconnected");
          this.mockMode = true;
        };
      } catch (e) {
        console.warn("[IPC] Connection failed — mock mode", e);
        this.mockMode = true;
        resolve();
      }
    });
  }

  /** Send a request to the backend and wait for a response. */
  async request<T>(command: string, payload?: unknown): Promise<T> {
    if (this.mockMode) {
      return this.mockResponse<T>(command, payload);
    }

    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        return resolve(this.mockResponse<T>(command, payload));
      }

      const id = crypto.randomUUID();
      const msg = JSON.stringify({ id, command, payload });

      const handler = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          if (data.id === id) {
            this.ws?.removeEventListener("message", handler);
            resolve(data.result as T);
          }
        } catch {
          // ignore malformed responses
        }
      };

      this.ws.addEventListener("message", handler);
      this.ws.send(msg);

      setTimeout(() => {
        this.ws?.removeEventListener("message", handler);
        resolve(this.mockResponse<T>(command, payload));
      }, 5000);
    });
  }

  /** Mock responses for development without a running backend. */
  private async mockResponse<T>(command: string, _payload?: unknown): Promise<T> {
    // Simulate network latency
    await new Promise((r) => setTimeout(r, 300 + Math.random() * 500));

    const mock: Record<string, unknown> = {
      get_mood_history: [
        { id: 1, timestamp: new Date(Date.now() - 3600000).toISOString(), valence: -0.2, arousal: 0.3, label: "anxious", confidence: 0.72, source: "ser" },
        { id: 2, timestamp: new Date(Date.now() - 1800000).toISOString(), valence: 0.1, arousal: 0.2, label: "neutral", confidence: 0.68, source: "ser" },
        { id: 3, timestamp: new Date().toISOString(), valence: -0.4, arousal: 0.7, label: "anxious", confidence: 0.85, source: "ser" },
      ] as MoodHistoryEntry[],
      run_demo: {
        spec: {
          mood_target: "anxious",
          intervention_mode: "nudge",
          narrative: "Take a deep breath. Let's bring that energy down with something grounding.",
          film_query: "mindful calming documentary",
          music_query: "ambient nature sounds meditation",
          light_scene: { scene_name: "calming", brightness: 80, color_temperature: 3500, transition_ms: 1000 },
          diffuser_profile: { oil_profile: "chamomile", duration_minutes: 30, intensity: 3 },
          movie: { title: "The Great Escape", year: 2024, overview: "A captivating journey...", poster_url: "", tmdb_id: 1, media_type: "movie", genre_ids: [12, 18], vote_average: 8.2 },
          playlists: [{ name: "Deep Focus", spotify_id: "dummy_0", url: "#", track_count: 50, tempo_range: [60, 80], valence_target: 0.4 }],
          available_devices: [],
        },
        emotion_state: { va: { valence: -0.4, arousal: 0.7 }, label: "anxious", confidence: 0.85, timestamp: new Date().toISOString(), source: "ser" },
        generated_at: new Date().toISOString(),
        pipeline_ms: 423,
      } as MashupResult,
      health: { status: "ok" },
    };

    return (mock[command] ?? { status: "unknown_command" }) as T;
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}

export const ipc = new IPCBridge();
