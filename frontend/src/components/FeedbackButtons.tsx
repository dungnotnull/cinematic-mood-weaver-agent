/** Feedback buttons — thumbs up/down and manual mood override for preference learning. */

import React, { useState } from "react";

interface FeedbackButtonsProps {
  onRating: (rating: 1 | 0 | -1) => void;
  onMoodOverride: (label: string) => void;
  disabled: boolean;
}

const MOOD_OPTIONS = [
  "happy",
  "calm",
  "neutral",
  "sad",
  "angry",
  "anxious",
  "surprised",
];

export function FeedbackButtons({ onRating, onMoodOverride, disabled }: FeedbackButtonsProps) {
  const [showOverride, setShowOverride] = useState(false);

  return (
    <div className="feedback-buttons">
      <p className="feedback-label">Was this mashup helpful?</p>

      <div className="rating-row">
        <button
          className="btn-feedback"
          disabled={disabled}
          onClick={() => onRating(1)}
          title="Thumbs up"
        >
          👍
        </button>

        <button
          className="btn-feedback"
          disabled={disabled}
          onClick={() => onRating(0)}
          title="Neutral"
        >
          🤷
        </button>

        <button
          className="btn-feedback"
          disabled={disabled}
          onClick={() => onRating(-1)}
          title="Thumbs down"
        >
          👎
        </button>

        <button
          className="btn-feedback btn-override"
          disabled={disabled}
          onClick={() => setShowOverride(!showOverride)}
        >
          ✏️ Override Mood
        </button>
      </div>

      {showOverride && (
        <div className="mood-override-picker">
          <p>What are you actually feeling?</p>
          <div className="mood-grid">
            {MOOD_OPTIONS.map((mood) => (
              <button
                key={mood}
                className="btn-mood"
                onClick={() => {
                  onMoodOverride(mood);
                  setShowOverride(false);
                }}
              >
                {mood}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
