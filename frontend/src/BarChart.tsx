type Bar = { label: string; value: number; detail?: string };

type Props = { title: string; caption: string; bars: Bar[] };

export default function BarChart({ title, caption, bars }: Props) {
  const max = Math.max(1, ...bars.map((bar) => bar.value));
  if (bars.length === 0) return null;
  return (
    <figure className="bars">
      <figcaption>
        <strong>{title}</strong>
        <span>{caption}</span>
      </figcaption>
      {bars.map((bar) => (
        <div className="bar-row" key={bar.label}>
          <span className="bar-label" title={bar.label}>
            {bar.label}
          </span>
          <div className="bar-track" role="img" aria-label={`${bar.label}: ${bar.detail || bar.value}`}>
            <div className="bar-fill" style={{ width: `${Math.max(4, (bar.value / max) * 100)}%` }} />
          </div>
          <span className="bar-value">{bar.detail || bar.value}</span>
        </div>
      ))}
    </figure>
  );
}
