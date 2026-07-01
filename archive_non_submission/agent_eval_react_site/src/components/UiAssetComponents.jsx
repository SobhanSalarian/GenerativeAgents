import React from "react";
import { uiAssets } from "./assetManifest";

export function BrandHeader() {
  return (
    <header className="brand-header">
      <a className="brand-lockup" href="#top" aria-label="AgentEval home">
        <img src={uiAssets.logo.src} alt={uiAssets.logo.label} />
        <span>
          <strong>AgentEval</strong>
          <small>Human evaluation console</small>
        </span>
      </a>
      <nav aria-label="Primary navigation">
        <a href="#briefing">Briefing</a>
        <a href="#workspace">Workspace</a>
        <a href="#rubrics">Rubrics</a>
      </nav>
      <span className="mode-pill">Masked trial mode</span>
    </header>
  );
}

export function HeroVisual() {
  return (
    <section className="hero-visual" aria-label="AgentEval overview visual">
      <img
        src={uiAssets.hero.src}
        alt="Human evaluation bridge between micro-level believability and macro-level coordination"
      />
    </section>
  );
}

export function RubricImageCard({ type = "micro" }) {
  const isMicro = type === "micro";
  return (
    <section className="rubric-image-card">
      <img
        src={isMicro ? uiAssets.banners.memoryPlanning : uiAssets.banners.macroCoordination}
        alt={isMicro ? "Memory planning and action flow" : "Macro-level coordination network"}
      />
      <div>
        <p className="eyebrow">{isMicro ? "Micro-level rubric" : "Macro-level rubric"}</p>
        <h3>
          {isMicro
            ? "Memory, planning and believability"
            : "Coordination, stability and role differentiation"}
        </h3>
        <p>
          {isMicro
            ? "Use these judgements to score behavioural consistency, memory coherence, planning plausibility and response naturalness."
            : "Use these judgements when reviewing aggregate outcomes, coordination success and system stability."}
        </p>
      </div>
    </section>
  );
}
