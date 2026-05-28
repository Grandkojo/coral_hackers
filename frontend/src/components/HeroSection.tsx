import type { ReactNode } from "react";
import SourceBadges from "./SourceBadges";

const WORKFLOW = [
  {
    step: "01",
    title: "Trigger",
    detail: "Describe the incident or paste a Vercel deploy link",
  },
  {
    step: "02",
    title: "Investigate",
    detail: "Coral SQL across GitHub, Sentry, Slack, and Vercel",
  },
  {
    step: "03",
    title: "Resolve",
    detail: "Review cited evidence and approve remediation when needed",
  },
] as const;

interface HeroSectionProps {
  alerts?: ReactNode;
  form: ReactNode;
}

export default function HeroSection({ alerts, form }: HeroSectionProps) {
  return (
    <section className="hero-landing">
      <div className="hero-glow" aria-hidden="true" />

      <div className="hero-landing-intro">
        <div className="hero-landing-copy">
          <p className="hero-eyebrow">Production incident intelligence</p>
          <h1 className="hero-headline">
            Find what broke across your stack
          </h1>
          <p className="hero-lead">
            One query, one report, optional remediation — correlated with Coral.
          </p>
        </div>
      </div>

      <div className="hero-landing-form-wrap">
        {alerts}
        {form}
      </div>

      <div className="hero-landing-support">
        <div className="hero-workflow">
          {WORKFLOW.map((item, index) => (
            <div
              key={item.step}
              className="workflow-step"
              style={{ animationDelay: `${index * 80}ms` }}
            >
              <span className="workflow-step-num">{item.step}</span>
              <div>
                <p className="workflow-step-title">{item.title}</p>
                <p className="workflow-step-detail">{item.detail}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="hero-sources">
          <span className="label block mb-3">Connected sources</span>
          <SourceBadges />
        </div>
      </div>
    </section>
  );
}
