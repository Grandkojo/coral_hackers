import { useState } from "react";
import type { DashboardTriggerRequest } from "../types/index";

interface InvestigationFormProps {
  onSubmit: (req: DashboardTriggerRequest) => void;
  isSubmitting: boolean;
  variant?: "default" | "hero";
}

const DEMO_SCENARIOS: Array<{
  label: string;
  payload: DashboardTriggerRequest;
}> = [
  {
    label: "Checkout 500s",
    payload: {
      query:
        "Why did checkout start returning 500 errors after the last production deploy?",
      incident_id: "DEMO-NL-001",
    },
  },
  {
    label: "Sentry spike",
    payload: {
      query:
        "Sentry errors spiked on python-fastapi after a Vercel deploy — find the regression.",
      incident_id: "DEMO-NL-002",
    },
  },
  {
    label: "Vercel deploy",
    payload: {
      vercel_url: "dpl_EEWWZ361mMHt6cnfxB3cFWQkChnv",
      query: "This reef deployment shows errors — investigate root cause.",
    },
  },
  {
    label: "Deploy ID only",
    payload: {
      vercel_url: "dpl_3NxkGF9TF2ArYH9z4suVWd27u7w9",
    },
  },
];

export default function InvestigationForm({
  onSubmit,
  isSubmitting,
  variant = "default",
}: InvestigationFormProps) {
  const [query, setQuery] = useState("");
  const [incidentId, setIncidentId] = useState("");
  const [vercelUrl, setVercelUrl] = useState("");

  const isValid = query.trim().length > 0 || vercelUrl.trim().length > 0;

  function applyScenario(payload: DashboardTriggerRequest) {
    setQuery(payload.query ?? "");
    setIncidentId(payload.incident_id ?? "");
    setVercelUrl(payload.vercel_url ?? "");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid || isSubmitting) return;
    onSubmit({
      query: query.trim(),
      incident_id: incidentId.trim() !== "" ? incidentId.trim() : undefined,
      vercel_url: vercelUrl.trim() !== "" ? vercelUrl.trim() : undefined,
      context: {},
    });
  }

  const isHero = variant === "hero";

  return (
    <form
      onSubmit={handleSubmit}
      className={`card launch-form ${isHero ? "launch-form-hero" : ""}`}
    >
      <div className="card-header">
        <div>
          <span
            className={`label block ${isHero ? "launch-form-kicker" : "mb-1"}`}
          >
            {isHero ? "Start here" : "Launch investigation"}
          </span>
          <span
            className={isHero ? "launch-form-headline" : "font-body text-sm"}
            style={isHero ? undefined : { color: "var(--ink-2)" }}
          >
            {isHero
              ? "Describe what broke across your stack"
              : "Start from natural language or a deployment link"}
          </span>
        </div>
        {!isHero ? (
          <span
            className="font-mono text-[0.56rem]"
            style={{ color: "var(--muted)" }}
          >
            POST /api/v1/triggers/dashboard
          </span>
        ) : null}
      </div>

      <div className="launch-form-body">
        <div className="space-y-2">
          <label className="label block">Quick demos</label>
          <div className="demo-chip-row">
            {DEMO_SCENARIOS.map((scenario) => (
              <button
                key={scenario.label}
                type="button"
                className="btn btn-secondary demo-chip"
                disabled={isSubmitting}
                onClick={() => applyScenario(scenario.payload)}
              >
                {scenario.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="label block" htmlFor="investigation-query">
            What happened?
          </label>
          <textarea
            id="investigation-query"
            className="field-input resize-none"
            rows={isHero ? 5 : 4}
            placeholder="Why did checkout fail after the last deploy?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isSubmitting}
          />
          <p className="field-hint">
            Describe the incident in plain English — GitHub, Sentry, Slack,
            and Vercel correlated via Coral.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="label block" htmlFor="vercel-url">
              Vercel deployment
            </label>
            <input
              id="vercel-url"
              type="text"
              className="field-input"
              placeholder="dpl_abc123 or full URL"
              value={vercelUrl}
              onChange={(e) => setVercelUrl(e.target.value)}
              disabled={isSubmitting}
            />
            <p className="field-hint">
              Optional — paste a deploy link to anchor the investigation
            </p>
          </div>

          <div className="space-y-2">
            <label className="label block" htmlFor="incident-id">
              Incident ID
            </label>
            <input
              id="incident-id"
              type="text"
              className="field-input"
              placeholder="PYTHON-FASTAPI-1"
              value={incidentId}
              onChange={(e) => setIncidentId(e.target.value)}
              disabled={isSubmitting}
            />
            <p className="field-hint">
              Optional — Sentry short ID or internal ticket ref
            </p>
          </div>
        </div>

        <div
          className={`launch-form-footer ${isHero ? "launch-form-footer-hero" : ""}`}
        >
          <span className="field-hint">
            {isValid
              ? "Ready to launch"
              : "Add a query or Vercel deployment to continue"}
          </span>
          <button
            type="submit"
            className={`btn btn-primary launch-submit ${isHero ? "launch-submit-hero" : ""}`}
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? "Investigating…" : "Launch investigation →"}
          </button>
        </div>
      </div>
    </form>
  );
}
