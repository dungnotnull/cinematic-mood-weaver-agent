/** TypeScript type definitions mirroring the Python Pydantic models. */

export interface ValenceArousal {
  valence: number; // -1 to +1
  arousal: number; // -1 to +1
}

export interface EmotionState {
  va: ValenceArousal;
  label: EmotionLabel;
  confidence: number;
  timestamp: string;
  source: "ser" | "biometric" | "fusion" | "manual";
}

export type EmotionLabel =
  | "happy"
  | "sad"
  | "angry"
  | "neutral"
  | "anxious"
  | "calm"
  | "surprised"
  | "disgust"
  | "fearful";

export type InterventionMode = "mirror" | "nudge" | "transform";

export interface LightScene {
  scene_name: string;
  brightness: number;
  color_temperature: number;
  transition_ms: number;
}

export interface DiffuserSchedule {
  oil_profile: string;
  duration_minutes: number;
  intensity: number;
}

export interface MovieRecommendation {
  title: string;
  year: number;
  overview: string;
  poster_url: string;
  tmdb_id: number;
  media_type: "movie" | "tv";
  genre_ids: number[];
  vote_average: number;
  streaming_url?: string;
}

export interface PlaylistRecommendation {
  name: string;
  spotify_id: string;
  url: string;
  track_count: number;
  tempo_range: [number, number];
  valence_target: number;
  image_url?: string;
}

export interface MashupSpec {
  mood_target: string;
  intervention_mode: InterventionMode;
  narrative: string;
  film_query: string;
  music_query: string;
  light_scene: LightScene;
  diffuser_profile: DiffuserSchedule;
  movie?: MovieRecommendation;
  playlists: PlaylistRecommendation[];
  available_devices: string[];
}

export interface MashupResult {
  spec: MashupSpec;
  emotion_state: EmotionState;
  generated_at: string;
  pipeline_ms: number;
}

export interface MoodHistoryEntry {
  id: number;
  timestamp: string;
  valence: number;
  arousal: number;
  label: EmotionLabel;
  confidence: number;
  source: string;
}
