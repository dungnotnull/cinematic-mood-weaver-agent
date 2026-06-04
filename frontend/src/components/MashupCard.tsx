/** Mashup Card component — displays the full multi-sensory recommendation bundle.

Shows the LLM-generated narrative, movie poster, playlist preview,
lighting swatch, and diffuser suggestion in a single organized card.
*/

import React from "react";
import type { MashupResult } from "../types";

interface MashupCardProps {
  result: MashupResult | null;
  loading: boolean;
}

const MODE_ICONS: Record<string, string> = {
  mirror: "🪞",
  nudge: "💨",
  transform: "🦋",
};

export function MashupCard({ result, loading }: MashupCardProps) {
  if (loading) {
    return (
      <div className="mashup-card loading">
        <div className="loading-spinner" />
        <p>Weaving your mood experience...</p>
        <div className="pipeline-timing">Pipeline running</div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="mashup-card empty">
        <p>Click "Generate Mashup" to create your first mood experience</p>
      </div>
    );
  }

  const { spec, emotion_state, pipeline_ms } = result;

  return (
    <div className={`mashup-card mode-${spec.intervention_mode}`}>
      {/* Header */}
      <div className="mashup-header">
        <span className="intervention-badge">
          {MODE_ICONS[spec.intervention_mode]} {spec.intervention_mode}
        </span>
        <span className="pipeline-timing">{pipeline_ms.toFixed(0)}ms</span>
      </div>

      {/* Narrative */}
      <blockquote className="narrative">"{spec.narrative}"</blockquote>

      {/* Content grid */}
      <div className="mashup-grid">
        {/* Movie */}
        <div className="mashup-item">
          <h4>🎬 Film</h4>
          {spec.movie ? (
            <>
              <p className="item-title">{spec.movie.title}</p>
              <p className="item-subtitle">
                {spec.movie.year} · {spec.movie.vote_average.toFixed(1)}/10
              </p>
              <p className="item-overview">{spec.movie.overview.slice(0, 120)}...</p>
            </>
          ) : (
            <p className="item-query">Searching: {spec.film_query}</p>
          )}
        </div>

        {/* Music */}
        <div className="mashup-item">
          <h4>🎵 Music</h4>
          {spec.playlists.length > 0 ? (
            <ul className="playlist-list">
              {spec.playlists.map((p, i) => (
                <li key={i}>
                  <a href={p.url} target="_blank" rel="noopener noreferrer">
                    {p.name}
                  </a>
                  <span className="track-count">{p.track_count} tracks</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="item-query">Searching: {spec.music_query}</p>
          )}
        </div>

        {/* Lighting */}
        <div className="mashup-item">
          <h4>💡 Lighting</h4>
          <div
            className="light-swatch"
            style={{ backgroundColor: temperatureToColor(spec.light_scene.color_temperature) }}
          />
          <p className="item-subtitle">
            {spec.light_scene.scene_name} · {spec.light_scene.color_temperature}K
          </p>
        </div>

        {/* Diffuser */}
        <div className="mashup-item">
          <h4>🌿 Aromatherapy</h4>
          <p className="item-title">{spec.diffuser_profile.oil_profile}</p>
          <p className="item-subtitle">
            {spec.diffuser_profile.duration_minutes}min · intensity{" "}
            {spec.diffuser_profile.intensity}/5
          </p>
        </div>
      </div>
    </div>
  );
}

function temperatureToColor(temp: number): string {
  // 2000K → orange, 4000K → neutral white, 6500K → cool blue
  if (temp <= 3000) return "#ffa05e";
  if (temp <= 4500) return "#ffe4b5";
  if (temp <= 5500) return "#fff8e7";
  return "#d4e4ff";
}
