function formatDate(value) {
  if (!value) return 'nicht angegeben';
  return new Intl.DateTimeFormat('de-DE').format(new Date(`${value}T12:00:00`));
}

export default function ContestCard({ contest, isFavorite, onToggleFavorite }) {
  return (
    <article className="contest-card">
      <div className="contest-card__topline">
        <span className="badge">Externe Aktion</span>
        {contest.verified && <span className="verified">✓ geprüft</span>}
      </div>
      <div className="contest-card__icon" aria-hidden="true">{contest.icon || '🍀'}</div>
      <p className="eyebrow">{contest.category}</p>
      <h2>{contest.title}</h2>
      <p className="prize">{contest.prize}</p>
      <p className="description">{contest.description}</p>
      <dl>
        <div><dt>Veranstalter</dt><dd>{contest.organizer}</dd></div>
        <div><dt>Teilnahmeschluss</dt><dd>{formatDate(contest.deadline)}</dd></div>
        <div><dt>Zuletzt geprüft</dt><dd>{formatDate(contest.lastChecked)}</dd></div>
      </dl>
      <div className="contest-card__actions">
        <a className="button button--primary" href={contest.sourceUrl} target="_blank" rel="noopener noreferrer nofollow">
          Zum offiziellen Gewinnspiel
        </a>
        <button className="button button--ghost" type="button" onClick={() => onToggleFavorite(contest.id)} aria-pressed={isFavorite}>
          {isFavorite ? '♥ Gemerkt' : '♡ Merken'}
        </button>
      </div>
      <p className="legal-note">LuckyPilot ist nicht Veranstalter. Es gelten die Bedingungen und Datenschutzhinweise des jeweiligen Veranstalters.</p>
    </article>
  );
}
