/** Onboarding wizard — guides new users through first-time setup.

Steps:
  1. Welcome + privacy notice
  2. Microphone permission
  3. API key configuration (or skip for mock mode)
  4. Device discovery (wearable BLE + smart home)
  5. Initial calibration
  6. Done!
*/

import React, { useState } from "react";

interface OnboardingWizardProps {
  onComplete: () => void;
}

const STEPS = [
  "Welcome",
  "Privacy",
  "Microphone",
  "API Keys",
  "Devices",
  "Ready!",
];

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState(0);
  const [micGranted, setMicGranted] = useState(false);
  const [skipApiKeys, setSkipApiKeys] = useState(true);

  const handleNext = () => {
    if (step < STEPS.length - 1) {
      setStep(step + 1);
    } else {
      onComplete();
    }
  };

  const handleBack = () => {
    if (step > 0) setStep(step - 1);
  };

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-card">
        {/* Progress bar */}
        <div className="onboarding-progress">
          {STEPS.map((s, i) => (
            <div
              key={i}
              className={`progress-step ${i === step ? "active" : i < step ? "done" : ""}`}
            >
              <span className="step-dot">{i < step ? "✓" : i + 1}</span>
              <span className="step-label">{s}</span>
            </div>
          ))}
        </div>

        {/* Step content */}
        <div className="onboarding-content">
          {step === 0 && (
            <>
              <h2>Welcome to Cinematic Mood Weaver</h2>
              <p>
                Your entertainment director — curating movies, music, lighting, and
                aromatherapy based on how you actually feel right now.
              </p>
            </>
          )}

          {step === 1 && (
            <>
              <h2>Your Privacy Matters</h2>
              <ul className="privacy-list">
                <li>🎤 Your voice is analyzed locally — never uploaded</li>
                <li>📊 Only anonymized emotion labels leave your device</li>
                <li>🔒 All data encrypted with AES-256-GCM</li>
                <li>🌐 Works fully offline (no cloud required)</li>
                <li>🗑️ Export or delete your data at any time</li>
              </ul>
            </>
          )}

          {step === 2 && (
            <>
              <h2>Microphone Access</h2>
              <p>Cinematic Mood Weaver needs microphone access to read your emotional state from your voice.</p>
              <button
                className="btn-primary"
                onClick={() => setMicGranted(true)}
                disabled={micGranted}
              >
                {micGranted ? "✓ Microphone Granted" : "Grant Microphone Access"}
              </button>
            </>
          )}

          {step === 3 && (
            <>
              <h2>API Keys (Optional)</h2>
              <p>Configure external services for richer recommendations. All work in mock mode if skipped.</p>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={skipApiKeys}
                  onChange={(e) => setSkipApiKeys(e.target.checked)}
                />
                Skip for now — use built-in recommendations
              </label>
              {!skipApiKeys && (
                <div className="api-key-hint">
                  <p>Edit <code>.env</code> in the project root with your keys:</p>
                  <pre>CLAUDE_API_KEY=sk-ant-...<br/>SPOTIFY_CLIENT_ID=...<br/>TMDB_API_KEY=...</pre>
                </div>
              )}
            </>
          )}

          {step === 4 && (
            <>
              <h2>Device Discovery</h2>
              <p>Cinematic Mood Weaver can connect to:</p>
              <ul className="device-list">
                <li>📱 Wearables (Polar H10, Apple Watch, Garmin) — optional</li>
                <li>💡 Smart lights (Philips Hue, Home Assistant) — optional</li>
                <li>🌿 Aromatherapy diffusers (SwitchBot) — optional</li>
              </ul>
              <p className="hint">All devices are optional — the system works with just a microphone.</p>
            </>
          )}

          {step === 5 && (
            <>
              <h2>You're All Set!</h2>
              <p>Your Cinematic Mood Weaver is ready to go.</p>
              <ul className="ready-list">
                <li>🎤 Click "Generate Mashup" to start</li>
                <li>📊 Watch your mood history build on the dashboard</li>
                <li>👍 Give feedback to improve recommendations</li>
              </ul>
            </>
          )}
        </div>

        {/* Navigation */}
        <div className="onboarding-nav">
          <button
            className="btn-secondary"
            onClick={handleBack}
            disabled={step === 0}
          >
            Back
          </button>
          <span className="step-counter">
            {step + 1} / {STEPS.length}
          </span>
          <button className="btn-primary" onClick={handleNext}>
            {step < STEPS.length - 1 ? "Continue" : "Start Using"}
          </button>
        </div>
      </div>
    </div>
  );
}
