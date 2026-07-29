import { useEffect, useMemo, useState } from 'react';
import Logo from './components/Logo.jsx';
import ContestCard from './components/ContestCard.jsx';

const categories = ['Alle', 'Reisen', 'Technik', 'Geld', 'Auto', 'Familie', 'Gaming', 'Einkauf', 'Sonstiges'];

export default function App() {
  const [contests, setContests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('Alle');
  const [favorites, setFavorites] = useState(() => JSON.parse(localStorage.getItem('luckypilot:favorites') || '[]'));

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/gewinnspiele.json`)
      .then((response) => {
        if (!response.ok) throw new Error('Die Gewinnspieldaten konnten nicht geladen werden.');
        return response.json();
      })
      .then((data) => setContests(Array.isArray(data) ? data : data.contests || []))
      .catch((reason) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    localStorage.setItem('luckypilot:favorites', JSON.stringify(favorites));
  }, [favorites]);

  const visibleContests = useMemo(() => {
    const term = query.trim().toLowerCase();
    return contests
      .filter((contest) => category === 'Alle' || contest.category === category)
      .filter((contest) => !term || [contest.title, contest.prize, contest.organizer, contest.description, contest.category]
        .join(' ').toLowerCase().includes(term))
      .sort((a, b) => new Date(a.deadline || '2999-12-31') - new Date(b.deadline || '2999-12-31'));
  }, [contests, category, query]);

  function toggleFavorite(id) {
    setFavorites((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  return (
    <>
      <header className="site-header" id="top">
        <div className="container site-header__inner">
          <Logo />
          <nav aria-label="Hauptnavigation">
            <a href="#gewinnspiele">Gewinnspiele</a>
            <a href="#hinweise">Hinweise</a>
          </nav>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="container hero__grid">
            <div>
              <span className="hero__label">Dein Navigator für seriöse Gewinnspiel-Links</span>
              <h1>Gewinnspiele finden, Fristen im Blick behalten.</h1>
              <p>LuckyPilot bündelt externe Aktionen übersichtlich und führt dich direkt zur offiziellen Veranstalterseite.</p>
            </div>
            <div className="hero__stats" aria-label="Übersicht">
              <div><strong>{contests.length}</strong><span>Einträge</span></div>
              <div><strong>{favorites.length}</strong><span>Favoriten</span></div>
              <div><strong>0</strong><span>automatische Teilnahmen</span></div>
            </div>
          </div>
        </section>

        <section className="container controls" id="gewinnspiele">
          <label className="search">
            <span>Gewinnspiel suchen</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="z. B. Reise, Technik oder Veranstalter" />
          </label>
          <div className="category-row" aria-label="Kategorien">
            {categories.map((item) => (
              <button key={item} className={category === item ? 'chip chip--active' : 'chip'} onClick={() => setCategory(item)} type="button">{item}</button>
            ))}
          </div>
        </section>

        <section className="container results" aria-live="polite">
          <div className="section-heading">
            <div><p className="eyebrow">Aktuelle Übersicht</p><h2>Externe Gewinnspiele</h2></div>
            <span>{visibleContests.length} Treffer</span>
          </div>
          {loading && <p className="status">Daten werden geladen …</p>}
          {error && <p className="status status--error">{error}</p>}
          {!loading && !error && visibleContests.length === 0 && <p className="status">Keine passenden Einträge gefunden.</p>}
          <div className="card-grid">
            {visibleContests.map((contest) => (
              <ContestCard key={contest.id} contest={contest} isFavorite={favorites.includes(contest.id)} onToggleFavorite={toggleFavorite} />
            ))}
          </div>
        </section>

        <section className="notice" id="hinweise">
          <div className="container notice__grid">
            <div><p className="eyebrow">Transparent und zurückhaltend</p><h2>LuckyPilot vermittelt nur.</h2></div>
            <p>Wir veranstalten keine der gelisteten Aktionen und geben keine Gewinnwahrscheinlichkeit an. Inhalte werden sachlich zusammengefasst; maßgeblich sind ausschließlich die Angaben auf der offiziellen Veranstalterseite.</p>
          </div>
        </section>
      </main>

      <footer>
        <div className="container footer__inner">
          <span>© {new Date().getFullYear()} LuckyPilot</span>
          <div><a href={`${import.meta.env.BASE_URL}legal/impressum.html`}>Impressum</a><a href={`${import.meta.env.BASE_URL}legal/datenschutz.html`}>Datenschutz</a><a href={`${import.meta.env.BASE_URL}legal/gewinnspielhinweise.html`}>Gewinnspielhinweise</a></div>
        </div>
      </footer>
    </>
  );
}
