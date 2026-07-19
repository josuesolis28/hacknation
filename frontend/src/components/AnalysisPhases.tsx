import { Language, copy } from "../i18n";

export type Stage = "initializing" | "detecting" | "analyzing_ux" | "validating" | "complete";

const ORDER: Stage[] = ["detecting", "analyzing_ux", "validating", "complete"];

export function AnalysisPhases({
  stage,
  language,
  progress,
}: {
  stage: Stage;
  language: Language;
  progress: number;
}) {
  const text = copy[language];
  const steps: { key: Stage; label: string; hint: string }[] = [
    { key: "detecting", label: text.scanning, hint: text.phaseScanningHint },
    { key: "analyzing_ux", label: text.phaseUx, hint: text.phaseUxHint },
    { key: "validating", label: text.validatingSignals, hint: text.phaseValidatingHint },
    { key: "complete", label: text.complete, hint: text.phaseCompleteHint },
  ];
  const currentIndex = ORDER.indexOf(stage === "initializing" ? "detecting" : stage);
  const pct = Math.max(0, Math.min(100, Math.round(progress)));

  return (
    <div className="phases">
      <div className="scan-progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="scan-progress-track">
          <div
            className={`scan-progress-fill ${stage === "complete" ? "done" : ""}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="scan-progress-pct">{pct}%</span>
      </div>
      <div className="phase-steps">
        {steps.map((step, i) => {
          const state = i < currentIndex ? "done" : i === currentIndex ? "active" : "pending";
          return (
            <div className={`phase-step ${state}`} key={step.key}>
              <div className="phase-dot">{state === "done" ? "✓" : i + 1}</div>
              <div className="phase-copy">
                <strong>{step.label}</strong>
                <span>{step.hint}</span>
              </div>
              {i < steps.length - 1 && <div className={`phase-line ${state === "done" ? "done" : ""}`} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
