export default function Logo() {
  return (
    <a className="brand" href="#top" aria-label="LuckyPilot Startseite">
      <svg className="brand__mark" viewBox="0 0 64 64" aria-hidden="true">
        <g fill="currentColor" transform="translate(31 30)">
          <circle cx="-10" cy="-10" r="11" />
          <circle cx="10" cy="-10" r="11" />
          <circle cx="-10" cy="10" r="11" />
          <circle cx="10" cy="10" r="11" />
        </g>
        <path d="M32 34c5 9 7 15 7 22" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
        <path d="M51 6l1.6 4.4L57 12l-4.4 1.6L51 17l-1.6-4.4L45 12l4.4-1.6z" fill="#d4af37" />
      </svg>
      <span><strong>Lucky</strong>Pilot<small>Damit dir kein Gewinnspiel entgeht.</small></span>
    </a>
  );
}
