/** React hook for the Cinematic Mood Weaver data layer.

Provides real-time emotion state, mood history, and mashup generation
via the IPC bridge (WebSocket mock or real backend).
*/

import { useCallback, useEffect, useState } from "react";
import type { EmotionState, MashupResult, MoodHistoryEntry } from "../types";
import { ipc } from "../utils/ipc";

interface MoodWeaverState {
  connected: boolean;
  loading: boolean;
  error: string | null;
  currentEmotion: EmotionState | null;
  moodHistory: MoodHistoryEntry[];
  currentMashup: MashupResult | null;
}

export function useMoodWeaver() {
  const [state, setState] = useState<MoodWeaverState>({
    connected: false,
    loading: false,
    error: null,
    currentEmotion: null,
    moodHistory: [],
    currentMashup: null,
  });

  useEffect(() => {
    ipc.connect().then(() => {
      setState((s) => ({ ...s, connected: !ipc.mockMode }));
    });
    return () => ipc.disconnect();
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      setState((s) => ({ ...s, loading: true }));
      const history = await ipc.request<MoodHistoryEntry[]>("get_mood_history");
      setState((s) => ({ ...s, moodHistory: history, loading: false }));
    } catch (err) {
      setState((s) => ({ ...s, error: String(err), loading: false }));
    }
  }, []);

  const runMashup = useCallback(async () => {
    try {
      setState((s) => ({ ...s, loading: true, error: null }));
      const result = await ipc.request<MashupResult>("run_demo");
      setState((s) => ({
        ...s,
        currentMashup: result,
        currentEmotion: result.emotion_state,
        moodHistory: [
          ...s.moodHistory,
          {
            id: Date.now(),
            timestamp: result.emotion_state.timestamp,
            valence: result.emotion_state.va.valence,
            arousal: result.emotion_state.va.arousal,
            label: result.emotion_state.label,
            confidence: result.emotion_state.confidence,
            source: result.emotion_state.source,
          },
        ],
        loading: false,
      }));
    } catch (err) {
      setState((s) => ({ ...s, error: String(err), loading: false }));
    }
  }, []);

  const clearError = useCallback(() => {
    setState((s) => ({ ...s, error: null }));
  }, []);

  return { ...state, fetchHistory, runMashup, clearError };
}
