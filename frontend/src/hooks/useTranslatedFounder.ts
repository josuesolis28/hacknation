import { useEffect, useState } from "react";
import { translateBatch } from "../api";
import { Language } from "../i18n";
import type { FounderProfile } from "../types";

export interface TranslatedFounderText {
  justification: string;
  activity_summary: string;
  pitch: string;
  other_info: string;
  impact_summary: string;
  capital_note: string;
  feedback: string[];
  criteriaRationale: string[];
  requirementDetail: string[];
}

function buildFields(founder: FounderProfile): string[] {
  return [
    founder.justification || "",
    founder.activity_summary || "",
    founder.pitch || "",
    founder.other_info || "",
    founder.impact_summary || "",
    founder.capital_note || "",
    ...founder.feedback,
    ...founder.criteria.map((c) => c.rationale || ""),
    ...founder.requirements.map((r) => r.detail || ""),
  ];
}

function unpack(founder: FounderProfile, values: string[]): TranslatedFounderText {
  let i = 0;
  const next = () => values[i++] ?? "";
  const justification = next();
  const activity_summary = next();
  const pitch = next();
  const other_info = next();
  const impact_summary = next();
  const capital_note = next();
  const feedback = founder.feedback.map(() => next());
  const criteriaRationale = founder.criteria.map(() => next());
  const requirementDetail = founder.requirements.map(() => next());
  return {
    justification,
    activity_summary,
    pitch,
    other_info,
    impact_summary,
    capital_note,
    feedback,
    criteriaRationale,
    requirementDetail,
  };
}

function original(founder: FounderProfile): TranslatedFounderText {
  return {
    justification: founder.justification || "",
    activity_summary: founder.activity_summary || "",
    pitch: founder.pitch || "",
    other_info: founder.other_info || "",
    impact_summary: founder.impact_summary || "",
    capital_note: founder.capital_note || "",
    feedback: founder.feedback,
    criteriaRationale: founder.criteria.map((c) => c.rationale || ""),
    requirementDetail: founder.requirements.map((r) => r.detail || ""),
  };
}

// Cache de proceso: una tarjeta + idioma solo dispara una llamada de
// traducción por lote, aunque el modal se abra/cierre varias veces.
const cache = new Map<string, TranslatedFounderText>();
// PitchPanel y el modal de la misma tarjeta pueden montarse casi al mismo
// tiempo (ambos llaman a este hook para el founder seleccionado). Sin este
// mapa, los dos disparaban su propia llamada a /api/translate/batch antes de
// que la primera terminara y llenara `cache` — duplicando tokens gastados
// por cada apertura. Ahora el segundo llamador espera la misma promesa.
const inflight = new Map<string, Promise<TranslatedFounderText>>();

/** Traduce en un solo request todos los campos de texto libre de un founder
 * (el backend genera justification/pitch/feedback/etc. siempre en español;
 * ver vcbrain/judge.py). Los nombres de criterios/requisitos NO pasan por
 * aquí: son un set fijo, ver criterionLabel/requirementLabel en i18n.ts. */
export function useTranslatedFounder(
  founder: FounderProfile | null,
  language: Language,
): TranslatedFounderText | null {
  const [result, setResult] = useState<TranslatedFounderText | null>(founder ? original(founder) : null);

  useEffect(() => {
    if (!founder) {
      setResult(null);
      return;
    }
    if (language === "es") {
      setResult(original(founder));
      return;
    }
    const key = `${founder.company}|${founder.name}|${language}`;
    const cached = cache.get(key);
    if (cached) {
      setResult(cached);
      return;
    }

    setResult(original(founder));
    let active = true;

    let promise = inflight.get(key);
    if (!promise) {
      promise = translateBatch(buildFields(founder), language).then(({ texts }) => unpack(founder, texts));
      inflight.set(key, promise);
      promise.finally(() => inflight.delete(key));
    }

    promise
      .then((unpacked) => {
        cache.set(key, unpacked);
        if (active) setResult(unpacked);
      })
      .catch(() => {
        if (active) setResult(original(founder));
      });

    return () => {
      active = false;
    };
  }, [founder, language]);

  return result;
}
