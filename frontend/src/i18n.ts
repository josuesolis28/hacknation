export type Language = "en" | "es" | "de";

export const LANGUAGES: Language[] = ["en", "es", "de"];

const STORAGE_KEY = "vcbrain_language";

export function loadLanguage(fallback: Language = "en"): Language {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "en" || saved === "es" || saved === "de") return saved;
  return fallback;
}

export function saveLanguage(language: Language) {
  localStorage.setItem(STORAGE_KEY, language);
}

type Dict = {
  title: string;
  subtitle: string;
  detected: string;
  validating: string;
  validated: string;
  logout: string;
  scope: string;
  scanning: string;
  validatingSignals: string;
  complete: string;
  collecting: string;
  analyzed: string;
  founderSignals: string;
  gatesMet: string;
  dealFlow: string;
  founders: string;
  profiles: string;
  analyzing: string;
  loginEyebrow: string;
  loginTitle: string;
  loginBlurb: string;
  user: string;
  password: string;
  access: string;
  authenticating: string;
  loginHint: string;
  approved: string;
  rejected: string;
  justification: string;
  criteria: string;
  weight: string;
  requirements: string;
  signals: string;
  evidence: string;
  issued: string;
  payTo: string;
  issueDate: string;
  instant: string;
  feedback: string;
  outreach: string;
  drafting: string;
  analyzeNetwork: string;
  origin: string;
  originConfirmed: string;
  originInferred: string;
  originUnknown: string;
  regionUS: string;
  regionEU: string;
  regionLATAM: string;
  regionUnknown: string;
  networkEmpty: string;
  networkLoading: string;
  networkCitations: string;
  source: string;
  roleTile: string;
  areaTile: string;
  skillsTile: string;
  socialsEyebrow: string;
  socialsTitle: string;
  socialsEmpty: string;
  openProfile: string;
  teamNodes: string;
  socialLinkedIn: string;
  socialInstagram: string;
  socialX: string;
  socialFacebook: string;
  socialGithub: string;
  socialWebsite: string;
  socialOther: string;
  fundInvite: string;
  metricsTitle: string;
  metricsEmpty: string;
  metricsHint: string;
  capitalRaised: string;
  publicSourcesOnly: string;
  noPublicData: string;
  businessModel: string;
  unknownModel: string;
  b2bB2cHint: string;
  clientsLabel: string;
  publicClientsHint: string;
  impactLabel: string;
  impactHint: string;
  tecBadge: string;
  companyName: string;
  businessEmail: string;
  sectionLabel: string;
  sectionHint: string;
  activityLabel: string;
  roundSize: string;
  roundHint: string;
  pitchLabel: string;
  otherInfo: string;
  otherInfoHint: string;
  trafficGreen: string;
  trafficYellow: string;
  trafficRed: string;
  trafficGreenDesc: string;
  trafficYellowDesc: string;
  trafficRedDesc: string;
  fundTeam: string;
  fundTeamEmpty: string;
  relFounder: string;
  relCofounder: string;
  relExecutive: string;
  relAdvisor: string;
  capitalTitle: string;
  totalCapitalLabel: string;
  fundingRoundsTitle: string;
  fundingRoundsEmpty: string;
  investorLabel: string;
  amountLabel: string;
  revenueLabel: string;
  revenueEmpty: string;
  clientsTitle: string;
  clientsEmpty: string;
};

export const copy: Record<Language, Dict> = {
  en: {
    title: "DACH startup intake",
    subtitle: "Germany · Switzerland · Austria — form-ready founder intelligence",
    detected: "Startups detected",
    validating: "Validating",
    validated: "Validated startups",
    logout: "Sign out",
    scope: "Based in Germany · Switzerland · Austria",
    scanning: "Scanning early-stage ecosystem",
    validatingSignals: "Validating signals and profiles",
    complete: "Analysis complete",
    collecting: "collecting sources",
    analyzed: "public sources analyzed",
    founderSignals: "founder and company signals",
    gatesMet: "all investment gates met",
    dealFlow: "DACH DEAL FLOW",
    founders: "DACH startups",
    profiles: "profiles",
    analyzing: "Analyzing automatically…",
    loginEyebrow: "MASCHMEYER GROUP · DACH MVP",
    loginTitle: "VC Brain",
    loginBlurb: "Secure intake intelligence for Germany, Switzerland and Austria.",
    user: "User",
    password: "Password",
    access: "Access workspace",
    authenticating: "Authenticating…",
    loginHint: "Local development access: admin12345 / admin12345",
    approved: "✓ APPROVED — $100K",
    rejected: "✗ NOT QUALIFIED",
    justification: "Justification",
    criteria: "Weighted criteria (pre-seed rubric)",
    weight: "weight",
    requirements: "Fund requirements",
    signals: "Technical signals",
    evidence: "Evidence",
    issued: "ISSUED",
    payTo: "Pay to the order of:",
    issueDate: "Issue date:",
    instant: "Instant approval · The VC Brain",
    feedback: "Automatic feedback — what is missing to qualify",
    outreach: "Generate personalized outreach",
    drafting: "Drafting…",
    analyzeNetwork: "Analyze profile nodes and sources",
    origin: "Origin",
    originConfirmed: "confirmed",
    originInferred: "inferred",
    originUnknown: "unknown",
    regionUS: "United States",
    regionEU: "Europe",
    regionLATAM: "Latin America",
    regionUnknown: "Unknown",
    networkEmpty: "Select a founder profile to see public social networks, or run “Analyze network” for a deeper map.",
    networkLoading: "Mapping public profile nodes and citations…",
    networkCitations: "Source citations",
    source: "Source",
    roleTile: "Role",
    areaTile: "Area",
    skillsTile: "Skills",
    socialsEyebrow: "PUBLIC NETWORKS",
    socialsTitle: "Social networks",
    socialsEmpty: "No public social URLs found yet. Run network analysis to enrich LinkedIn, Instagram or X.",
    openProfile: "Open",
    teamNodes: "Team nodes",
    socialLinkedIn: "LinkedIn",
    socialInstagram: "Instagram",
    socialX: "X",
    socialFacebook: "Facebook",
    socialGithub: "GitHub",
    socialWebsite: "Website",
    socialOther: "Other",
    fundInvite: "INTAKE FORM · PUBLIC SIGNALS",
    metricsTitle: "Company, email, section, round and pitch",
    metricsEmpty: "Select a DACH startup on the left to fill the intake fields.",
    metricsHint: "Public signals mapped to the fund intake form.",
    capitalRaised: "Capital raised",
    publicSourcesOnly: "from public sources only",
    noPublicData: "No public data",
    businessModel: "Business model",
    unknownModel: "Unknown",
    b2bB2cHint: "B2B · B2C · hybrid relations",
    clientsLabel: "Clients / relations",
    publicClientsHint: "named clients or segments when public",
    impactLabel: "Demonstrated impact",
    impactHint: "users, pilots, revenue or stated outcomes",
    tecBadge: "Tec de Monterrey",
    companyName: "Company name",
    businessEmail: "Business email",
    sectionLabel: "Section",
    sectionHint: "HealthTech, FinTech, Food & AgTech, …",
    activityLabel: "What the company does",
    roundSize: "Round size (raising)",
    roundHint: "< EUR 1 mio … > EUR 5 mio",
    pitchLabel: "Pitch",
    otherInfo: "Other information",
    otherInfoHint: "Extra public context if available",
    trafficGreen: "Candidate",
    trafficYellow: "Potential",
    trafficRed: "Not qualified",
    trafficGreenDesc: "Meets all fund gates and rubric threshold",
    trafficYellowDesc: "Shows potential but does not fully qualify yet",
    trafficRedDesc: "Does not meet the fund's base criteria",
    fundTeam: "Founders & cofounders",
    fundTeamEmpty: "No team members identified in public sources yet.",
    relFounder: "Founder",
    relCofounder: "Cofounder",
    relExecutive: "Executive",
    relAdvisor: "Advisor",
    capitalTitle: "Capital & funds",
    totalCapitalLabel: "Total capital raised",
    fundingRoundsTitle: "Participating funds / investors",
    fundingRoundsEmpty: "No public funding rounds found.",
    investorLabel: "Investor",
    amountLabel: "Amount",
    revenueLabel: "Revenue / traction",
    revenueEmpty: "No public revenue signal",
    clientsTitle: "Clients & revenue signal",
    clientsEmpty: "No named clients found in public sources.",
  },
  es: {
    title: "Intake startups DACH",
    subtitle: "Alemania · Suiza · Austria — inteligencia alineada al formulario",
    detected: "Startups detectadas",
    validating: "En validación",
    validated: "Startups validadas",
    logout: "Salir",
    scope: "Based in Germany · Switzerland · Austria",
    scanning: "Explorando el ecosistema early-stage",
    validatingSignals: "Validando señales y perfiles",
    complete: "Análisis completo",
    collecting: "recolectando fuentes",
    analyzed: "fuentes públicas analizadas",
    founderSignals: "señales de fundador y empresa",
    gatesMet: "todos los requisitos del fondo cumplidos",
    dealFlow: "DEAL FLOW DACH",
    founders: "Startups DACH",
    profiles: "perfiles",
    analyzing: "Analizando automáticamente…",
    loginEyebrow: "MASCHMEYER GROUP · MVP DACH",
    loginTitle: "VC Brain",
    loginBlurb: "Inteligencia de intake para Alemania, Suiza y Austria.",
    user: "Usuario",
    password: "Contraseña",
    access: "Acceder al workspace",
    authenticating: "Autenticando…",
    loginHint: "Acceso local de desarrollo: admin12345 / admin12345",
    approved: "✓ APROBADO — $100K",
    rejected: "✗ NO CALIFICA",
    justification: "Justificación",
    criteria: "Criterios ponderados (rúbrica pre-seed)",
    weight: "peso",
    requirements: "Requisitos del fondo",
    signals: "Señales técnicas",
    evidence: "Evidencia",
    issued: "EMITIDO",
    payTo: "Páguese a la orden de:",
    issueDate: "Fecha de emisión:",
    instant: "Aprobación instantánea · The VC Brain",
    feedback: "Feedback automático — qué falta para calificar",
    outreach: "Generar outreach personalizado",
    drafting: "Redactando…",
    analyzeNetwork: "Analizar nodos de perfil y fuentes",
    origin: "Origen",
    originConfirmed: "confirmado",
    originInferred: "inferido",
    originUnknown: "desconocido",
    regionUS: "EE. UU.",
    regionEU: "Europa",
    regionLATAM: "Latinoamérica",
    regionUnknown: "Desconocido",
    networkEmpty: "Selecciona un perfil a la izquierda para ver redes sociales públicas, o ejecuta “Analizar red” para un mapa más profundo.",
    networkLoading: "Mapeando nodos de perfil públicos y citas…",
    networkCitations: "Citas de fuentes",
    source: "Fuente",
    roleTile: "Rol",
    areaTile: "Área",
    skillsTile: "Habilidades",
    socialsEyebrow: "REDES PÚBLICAS",
    socialsTitle: "Redes sociales",
    socialsEmpty: "Aún no hay URLs sociales públicas. Analiza la red para enriquecer LinkedIn, Instagram o X.",
    openProfile: "Abrir",
    teamNodes: "Nodos del equipo",
    socialLinkedIn: "LinkedIn",
    socialInstagram: "Instagram",
    socialX: "X",
    socialFacebook: "Facebook",
    socialGithub: "GitHub",
    socialWebsite: "Sitio web",
    socialOther: "Otra",
    fundInvite: "FORMULARIO DE INTAKE · SEÑALES PÚBLICAS",
    metricsTitle: "Empresa, email, sección, ronda y pitch",
    metricsEmpty: "Selecciona una startup DACH a la izquierda para completar los campos del formulario.",
    metricsHint: "Señales públicas mapeadas al formulario del fondo.",
    capitalRaised: "Capital levantado",
    publicSourcesOnly: "solo fuentes públicas",
    noPublicData: "Sin dato público",
    businessModel: "Modelo de negocio",
    unknownModel: "Desconocido",
    b2bB2cHint: "Relaciones B2B · B2C · híbridas",
    clientsLabel: "Clientes / relaciones",
    publicClientsHint: "clientes o segmentos cuando son públicos",
    impactLabel: "Impacto demostrado",
    impactHint: "usuarios, pilots, ingresos o resultados declarados",
    tecBadge: "Tec de Monterrey",
    companyName: "Nombre de la empresa",
    businessEmail: "Email de negocio",
    sectionLabel: "Sección",
    sectionHint: "HealthTech, FinTech, Food & AgTech, …",
    activityLabel: "A qué se dedica",
    roundSize: "Tamaño de ronda (raising)",
    roundHint: "< EUR 1 mio … > EUR 5 mio",
    pitchLabel: "Pitch",
    otherInfo: "Otra información",
    otherInfoHint: "Contexto público adicional si existe",
    trafficGreen: "Candidato",
    trafficYellow: "Con potencial",
    trafficRed: "No califica",
    trafficGreenDesc: "Cumple todos los requisitos y el umbral de la rúbrica",
    trafficYellowDesc: "Muestra potencial pero todavía no califica del todo",
    trafficRedDesc: "No cumple los criterios base del fondo",
    fundTeam: "Founders y cofounders",
    fundTeamEmpty: "Aún no se identifican miembros del equipo en fuentes públicas.",
    relFounder: "Founder",
    relCofounder: "Cofounder",
    relExecutive: "Ejecutivo",
    relAdvisor: "Advisor",
    capitalTitle: "Capital y fondos",
    totalCapitalLabel: "Capital total levantado",
    fundingRoundsTitle: "Fondos / inversionistas participantes",
    fundingRoundsEmpty: "No se encontraron rondas de inversión públicas.",
    investorLabel: "Inversionista",
    amountLabel: "Monto",
    revenueLabel: "Revenue / tracción",
    revenueEmpty: "Sin señal pública de revenue",
    clientsTitle: "Clientes y señal de revenue",
    clientsEmpty: "No se encontraron clientes nombrados en fuentes públicas.",
  },
  de: {
    title: "DACH Startup Intake",
    subtitle: "Deutschland · Schweiz · Österreich — formularbereit",
    detected: "Erkannte Startups",
    validating: "In Prüfung",
    validated: "Validierte Startups",
    logout: "Abmelden",
    scope: "Based in Germany · Switzerland · Austria",
    scanning: "Early-Stage-Ökosystem wird gescannt",
    validatingSignals: "Signale und Profile werden geprüft",
    complete: "Analyse abgeschlossen",
    collecting: "Quellen werden gesammelt",
    analyzed: "öffentliche Quellen analysiert",
    founderSignals: "Founder- und Unternehmenssignale",
    gatesMet: "alle Investment-Gates erfüllt",
    dealFlow: "DACH DEAL FLOW",
    founders: "DACH Startups",
    profiles: "Profile",
    analyzing: "Automatische Analyse…",
    loginEyebrow: "MASCHMEYER GROUP · DACH MVP",
    loginTitle: "VC Brain",
    loginBlurb: "Sichere Intake-Intelligence für Deutschland, Schweiz und Österreich.",
    user: "Benutzer",
    password: "Passwort",
    access: "Workspace öffnen",
    authenticating: "Authentifizierung…",
    loginHint: "Lokaler Entwicklungszugang: admin12345 / admin12345",
    approved: "✓ GENEHMIGT — $100K",
    rejected: "✗ NICHT QUALIFIZIERT",
    justification: "Begründung",
    criteria: "Gewichtete Kriterien (Pre-Seed-Rubrik)",
    weight: "Gewicht",
    requirements: "Fonds-Anforderungen",
    signals: "Technische Signale",
    evidence: "Evidenz",
    issued: "AUSGESTELLT",
    payTo: "Zahlbar an die Order von:",
    issueDate: "Ausstellungsdatum:",
    instant: "Sofortige Freigabe · The VC Brain",
    feedback: "Automatisches Feedback — was zur Qualifikation fehlt",
    outreach: "Personalisierte Outreach erstellen",
    drafting: "Wird erstellt…",
    analyzeNetwork: "Profilknoten und Quellen analysieren",
    origin: "Herkunft",
    originConfirmed: "bestätigt",
    originInferred: "abgeleitet",
    originUnknown: "unbekannt",
    regionUS: "USA",
    regionEU: "Europa",
    regionLATAM: "Lateinamerika",
    regionUnknown: "Unbekannt",
    networkEmpty: "Wähle links ein Founder-Profil, um öffentliche Social Networks zu sehen, oder starte „Netzwerk analysieren“ für eine tiefere Karte.",
    networkLoading: "Öffentliche Profilknoten und Zitate werden gemappt…",
    networkCitations: "Quellenangaben",
    source: "Quelle",
    roleTile: "Rolle",
    areaTile: "Bereich",
    skillsTile: "Skills",
    socialsEyebrow: "ÖFFENTLICHE NETZWERKE",
    socialsTitle: "Social Networks",
    socialsEmpty: "Noch keine öffentlichen Social-URLs. Netzwerkanalyse anstoßen, um LinkedIn, Instagram oder X zu ergänzen.",
    openProfile: "Öffnen",
    teamNodes: "Team-Knoten",
    socialLinkedIn: "LinkedIn",
    socialInstagram: "Instagram",
    socialX: "X",
    socialFacebook: "Facebook",
    socialGithub: "GitHub",
    socialWebsite: "Website",
    socialOther: "Andere",
    fundInvite: "INTAKE-FORMULAR · ÖFFENTLICHE SIGNALE",
    metricsTitle: "Unternehmen, E-Mail, Sektion, Runde und Pitch",
    metricsEmpty: "Wähle links ein DACH-Startup, um die Formularfelder zu füllen.",
    metricsHint: "Öffentliche Signale gemappt auf das Fonds-Formular.",
    capitalRaised: "Eingeworbenes Kapital",
    publicSourcesOnly: "nur öffentliche Quellen",
    noPublicData: "Keine öffentlichen Daten",
    businessModel: "Geschäftsmodell",
    unknownModel: "Unbekannt",
    b2bB2cHint: "B2B · B2C · hybride Beziehungen",
    clientsLabel: "Kunden / Beziehungen",
    publicClientsHint: "genannte Kunden oder Segmente, wenn öffentlich",
    impactLabel: "Nachgewiesener Impact",
    impactHint: "Nutzer, Pilots, Umsatz oder genannte Outcomes",
    tecBadge: "Tec de Monterrey",
    companyName: "Firmenname",
    businessEmail: "Geschäftliche E-Mail",
    sectionLabel: "Sektion",
    sectionHint: "HealthTech, FinTech, Food & AgTech, …",
    activityLabel: "Womit sich das Unternehmen beschäftigt",
    roundSize: "Rundengröße (raising)",
    roundHint: "< EUR 1 mio … > EUR 5 mio",
    pitchLabel: "Pitch",
    otherInfo: "Weitere Informationen",
    otherInfoHint: "Zusätzlicher öffentlicher Kontext, falls vorhanden",
    trafficGreen: "Kandidat",
    trafficYellow: "Potenzial",
    trafficRed: "Nicht qualifiziert",
    trafficGreenDesc: "Erfüllt alle Fonds-Gates und die Rubrik-Schwelle",
    trafficYellowDesc: "Zeigt Potenzial, qualifiziert sich aber noch nicht vollständig",
    trafficRedDesc: "Erfüllt die Basiskriterien des Fonds nicht",
    fundTeam: "Founder & Cofounder",
    fundTeamEmpty: "In öffentlichen Quellen wurden noch keine Teammitglieder identifiziert.",
    relFounder: "Founder",
    relCofounder: "Cofounder",
    relExecutive: "Führungskraft",
    relAdvisor: "Advisor",
    capitalTitle: "Kapital & Fonds",
    totalCapitalLabel: "Insgesamt eingeworbenes Kapital",
    fundingRoundsTitle: "Beteiligte Fonds / Investoren",
    fundingRoundsEmpty: "Keine öffentlichen Finanzierungsrunden gefunden.",
    investorLabel: "Investor",
    amountLabel: "Betrag",
    revenueLabel: "Umsatz / Traktion",
    revenueEmpty: "Kein öffentliches Umsatzsignal",
    clientsTitle: "Kunden & Umsatzsignal",
    clientsEmpty: "Keine namentlich genannten Kunden in öffentlichen Quellen gefunden.",
  },
};

export function originLabel(founder: {
  country?: string;
  country_code?: string;
  origin_region?: string;
}, language: Language): string {
  const t = copy[language];
  if (founder.country) return founder.country;
  if (founder.country_code === "DE") return "Germany";
  if (founder.country_code === "CH") return "Switzerland";
  if (founder.country_code === "AT") return "Austria";
  if (founder.country_code === "US") return t.regionUS;
  switch (founder.origin_region) {
    case "DACH": return "DACH";
    case "United States": return t.regionUS;
    case "Europe": return t.regionEU;
    case "Latin America": return t.regionLATAM;
    default: return t.regionUnknown;
  }
}

export function confidenceLabel(confidence: string | undefined, language: Language): string {
  const t = copy[language];
  if (confidence === "confirmed") return t.originConfirmed;
  if (confidence === "inferred") return t.originInferred;
  return t.originUnknown;
}

export function trafficLabel(light: string | undefined, language: Language): string {
  const t = copy[language];
  if (light === "green") return t.trafficGreen;
  if (light === "yellow") return t.trafficYellow;
  return t.trafficRed;
}

export function trafficDescription(light: string | undefined, language: Language): string {
  const t = copy[language];
  if (light === "green") return t.trafficGreenDesc;
  if (light === "yellow") return t.trafficYellowDesc;
  return t.trafficRedDesc;
}

export function relationshipLabel(relationship: string | undefined, language: Language): string {
  const t = copy[language];
  switch (relationship) {
    case "cofounder": return t.relCofounder;
    case "executive": return t.relExecutive;
    case "advisor": return t.relAdvisor;
    default: return t.relFounder;
  }
}
