/** Mood Dashboard component — real-time valence-arousal plot + emotion label.

Displays the current emotional state on a 2D circumplex model and
shows recent mood history as a trend line using Recharts.
*/

import React from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EmotionState, MoodHistoryEntry } from "../types";

interface MoodDashboardProps {
  currentEmotion: EmotionState | null;
  moodHistory: MoodHistoryEntry[];
  loading: boolean;
}

const EMOTION_COLORS: Record<string, string> = {
  happy: "#fbbf24",
  sad: "#6366f1",
  angry: "#ef4444",
  neutral: "#9ca3af",
  anxious: "#f97316",
  calm: "#22c55e",
  surprised: "#a855f7",
  disgust: "#84cc16",
  fearful: "#e11d48",
};

export function MoodDashboard({ currentEmotion, moodHistory, loading }: MoodDashboardProps) {
  const chartData = moodHistory.map((e) => ({
    time: new Date(e.timestamp).toLocaleTimeString(),
    valence: e.valence,
    arousal: e.arousal,
  }));

  return (
    <div className="mood-dashboard">
      <h2 className="dashboard-title">Mood Dashboard</h2>

      {/* Current emotion card */}
      <div className="current-emotion-card">
        {loading && <div className="loading-spinner" />}
        {currentEmotion ? (
          <>
            <div
              className="emotion-indicator"
              style={{
                backgroundColor:
                  EMOTION_COLORS[currentEmotion.label] ?? "#9ca3af",
              }}
            >
              <span className="emotion-label">{currentEmotion.label}</span>
            </div>
            <div className="emotion-details">
              <p>
                <strong>Valence:</strong> {currentEmotion.va.valence.toFixed(2)}
              </p>
              <p>
                <strong>Arousal:</strong> {currentEmotion.va.arousal.toFixed(2)}
              </p>
              <p>
                <strong>Confidence:</strong>{" "}
                {(currentEmotion.confidence * 100).toFixed(0)}%
              </p>
              <p>
                <strong>Source:</strong> {currentEmotion.source}
              </p>
            </div>
          </>
        ) : (
          <p className="no-data">No emotion data yet — run a mashup to begin</p>
        )}
      </div>

      {/* Valence-Arousal trend chart */}
      <div className="trend-chart">
        <h3>Mood Trend (Last {moodHistory.length} samples)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" fontSize={11} />
            <YAxis domain={[-1, 1]} fontSize={11} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="valence"
              stroke="#22c55e"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="Valence"
            />
            <Line
              type="monotone"
              dataKey="arousal"
              stroke="#f97316"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="Arousal"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
