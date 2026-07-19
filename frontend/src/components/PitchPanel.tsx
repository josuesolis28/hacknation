import type { FounderProfile } from "../types";
import { Language, copy } from "../i18n";
import { useTranslatedFounder } from "../hooks/useTranslatedFounder";

export function PitchPanel({ founder, language }: { founder: FounderProfile | null; language: Language }) {
  const text = copy[language];
  const translated = useTranslatedFounder(founder, language);

  if (!founder) {
    return <aside className="network-panel empty-panel">{text.pitchPanelEmpty}</aside>;
  }

  const pitch = translated?.pitch || translated?.activity_summary || text.pitchPanelEmpty;

  return (
    <aside className="network-panel">
      <span className="eyebrow">{text.pitchPanelEyebrow}</span>
      <h2>{founder.company}</h2>
      <p className="network-summary">{pitch}</p>
    </aside>
  );
}
