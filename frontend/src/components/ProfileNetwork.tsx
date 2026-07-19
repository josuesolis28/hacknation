import type { FounderProfile, ProfileNetwork, SocialLink } from "../types";
import { Language, copy } from "../i18n";

function platformLabel(platform: string, text: (typeof copy)[Language]): string {
  const key = platform.toLowerCase();
  if (key === "linkedin") return text.socialLinkedIn;
  if (key === "instagram") return text.socialInstagram;
  if (key === "x" || key === "twitter") return text.socialX;
  if (key === "facebook") return text.socialFacebook;
  if (key === "github") return text.socialGithub;
  if (key === "website") return text.socialWebsite;
  return platform || text.socialOther;
}

function mergeSocials(founder: FounderProfile | null, network: ProfileNetwork | null): SocialLink[] {
  const map = new Map<string, SocialLink>();
  for (const link of [...(founder?.social_links || []), ...(network?.social_links || [])]) {
    if (link?.url) map.set(link.url, link);
  }
  return [...map.values()];
}

export function ProfileNetworkView({
  founder,
  network,
  loading,
  error,
  language,
}: {
  founder: FounderProfile | null;
  network: ProfileNetwork | null;
  loading: boolean;
  error: string | null;
  language: Language;
}) {
  const text = copy[language];
  const socials = mergeSocials(founder, network);

  if (!founder && !network && !loading && !error) {
    return <aside className="network-panel empty-panel">{text.networkEmpty}</aside>;
  }
  if (loading) {
    return (
      <aside className="network-panel loading-panel">
        <span className="spinner" /> {text.networkLoading}
      </aside>
    );
  }
  if (error) {
    return (
      <aside className="network-panel">
        <p className="form-error">{error}</p>
      </aside>
    );
  }

  const subject = network?.subject || (founder ? { name: founder.name, company: founder.company, role: founder.role } : null);

  return (
    <aside className="network-panel">
      <span className="eyebrow">{text.socialsEyebrow}</span>
      <h2>{subject?.company || text.socialsTitle}</h2>
      {network?.summary && <p className="network-summary">{network.summary}</p>}

      <h3 className="panel-subtitle">{text.socialsTitle}</h3>
      {socials.length === 0 ? (
        <p className="muted">{text.socialsEmpty}</p>
      ) : (
        <div className="social-grid">
          {socials.map((link) => (
            <a
              className={`social-card platform-${(link.platform || "other").toLowerCase()}`}
              key={link.url}
              href={link.url}
              target="_blank"
              rel="noreferrer"
            >
              <span>{platformLabel(link.platform, text)}</span>
              <strong>{link.label || platformLabel(link.platform, text)}</strong>
              <small>{text.openProfile} ↗</small>
            </a>
          ))}
        </div>
      )}

      {network && network.nodes.length > 0 && (
        <>
          <h3 className="panel-subtitle">{text.teamNodes}</h3>
          <div className="node-map">
            {network.nodes.map((node, index) => (
              <article className="profile-node" key={`${node.name}-${index}`}>
                <span>{node.relationship}</span>
                <h3>{node.name}</h3>
                <strong>{node.role}</strong>
                {node.area && <em className="node-area">{node.area}</em>}
                <p>{node.description}</p>
                {node.skills && node.skills.length > 0 && (
                  <div className="skill-chips">
                    {node.skills.map((skill) => (
                      <span className="skill-chip" key={skill}>
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
                {node.sources?.map((url) => (
                  <a key={url} href={url} target="_blank" rel="noreferrer">
                    {text.source} ↗
                  </a>
                ))}
              </article>
            ))}
          </div>
        </>
      )}

      {network && network.citations.length > 0 && (
        <>
          <h3 className="citation-title">{text.networkCitations}</h3>
          {network.citations.map((citation) => (
            <a className="citation" key={citation.url} href={citation.url} target="_blank" rel="noreferrer">
              {citation.title || citation.url} ↗
            </a>
          ))}
        </>
      )}
    </aside>
  );
}
