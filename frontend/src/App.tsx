/** Main App component — orchestrates the mood dashboard, mashup card, and feedback. */

import React from "react";
import { FeedbackButtons } from "./components/FeedbackButtons";
import { MashupCard } from "./components/MashupCard";
import { MoodDashboard } from "./components/MoodDashboard";
import { useMoodWeaver } from "./hooks/useMoodWeaver";

function App() {
  const {
    connected,
    loading,
    error,
    currentEmotion,
    moodHistory,
    currentMashup,
    fetchHistory,
    runMashup,
    clearError,
  } = useMoodWeaver();

  React.useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Cinematic Mood Weaver</h1>
        <p className="tagline">Your Entertainment Director — Curated by Your Real-Time Emotional State</p>
        <div className="status-bar">
          <span className={`status-dot ${connected ? "online" : "offline"}`} />
          <span>{connected ? "Backend connected" : "Mock mode (no backend)"}</span>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={clearError}>✕</button>
        </div>
      )}

      <main className="app-main">
        <section className="dashboard-section">
          <MoodDashboard
            currentEmotion={currentEmotion}
            moodHistory={moodHistory}
            loading={loading}
          />
        </section>

        <section className="mashup-section">
          <div className="mashup-controls">
            <button
              className="btn-primary"
              onClick={runMashup}
              disabled={loading}
            >
              {loading ? "Weaving..." : "Generate Mashup"}
            </button>
          </div>

          <MashupCard result={currentMashup} loading={loading} />
        </section>

        <section className="feedback-section">
          <FeedbackButtons
            onRating={(r) => console.log("Rating:", r)}
            onMoodOverride={(m) => console.log("Mood override:", m)}
            disabled={loading || !currentMashup}
          />
        </section>
      </main>

      <footer className="app-footer">
        <p>All emotion data processed locally · No audio or biometrics transmitted externally</p>
      </footer>
    </div>
  );
}

export default App;
