type Point = { x: number; yCount: number; yPos: number | null; label: string };

type Props = {
  points: Point[];
  showCount: boolean;
  showPos: boolean;
};

export default function LineChart({ points, showCount, showPos }: Props) {
  const width = 640;
  const height = 280;
  const pad = { l: 44, r: 44, t: 16, b: 36 };
  const innerW = width - pad.l - pad.r;
  const innerH = height - pad.t - pad.b;
  if (points.length === 0) {
    return <p className="muted">No chart points for this selection.</p>;
  }
  const xs = points.map((p) => p.x);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const spanX = maxX === minX ? 1 : maxX - minX;
  const counts = points.map((p) => p.yCount);
  const maxC = Math.max(1, ...counts);
  const positions = points.map((p) => p.yPos).filter((v): v is number => v != null);
  const maxP = positions.length ? Math.max(1, ...positions) : 1;
  const xAt = (x: number) => pad.l + ((x - minX) / spanX) * innerW;
  const yCount = (v: number) => pad.t + innerH - (v / maxC) * innerH;
  const yPos = (v: number) => pad.t + (v / maxP) * innerH;
  const countPath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xAt(p.x).toFixed(1)} ${yCount(p.yCount).toFixed(1)}`)
    .join(" ");
  const posPts = points.filter((p) => p.yPos != null);
  const posPath = posPts
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xAt(p.x).toFixed(1)} ${yPos(p.yPos as number).toFixed(1)}`)
    .join(" ");

  return (
    <>
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img">
      {[0, 0.5, 1].map((t) => (
        <line
          key={t}
          className="grid"
          x1={pad.l}
          x2={width - pad.r}
          y1={pad.t + innerH * t}
          y2={pad.t + innerH * t}
        />
      ))}
      {showCount ? <path d={countPath} className="series-count" /> : null}
      {showPos && posPath ? <path d={posPath} className="series-pos" /> : null}
      {showCount
        ? points.map((p) => (
            <circle key={`c-${p.label}`} className="dot-count" cx={xAt(p.x)} cy={yCount(p.yCount)} r={3}>
              <title>{`${p.label}: playlist count ${p.yCount}`}</title>
            </circle>
          ))
        : null}
      {showPos
        ? posPts.map((p) => (
            <circle key={`p-${p.label}`} className="dot-pos" cx={xAt(p.x)} cy={yPos(p.yPos as number)} r={3}>
              <title>{`${p.label}: best position ${p.yPos}`}</title>
            </circle>
          ))
        : null}
      {points.map((p) => (
        <text key={`t-${p.label}`} className="axis" x={xAt(p.x)} y={height - 10} textAnchor="middle">
          {p.label}
        </text>
      ))}
      {showCount && points.length <= 8
        ? points.map((p) => (
            <text key={`cv-${p.label}`} className="axis" x={xAt(p.x) + 6} y={yCount(p.yCount) - 6}>
              {p.yCount}
            </text>
          ))
        : null}
      {showPos && posPts.length <= 8
        ? posPts.map((p) => (
            <text key={`pv-${p.label}`} className="axis" x={xAt(p.x) + 6} y={yPos(p.yPos as number) - 6}>
              {p.yPos}
            </text>
          ))
        : null}
      {showCount ? (
        <text className="axis" x={pad.l} y={12}>
          Playlist count
        </text>
      ) : null}
      {showPos ? (
        <text className="axis" x={width - pad.r} y={12} textAnchor="end">
          Best position
        </text>
      ) : null}
    </svg>
    {points.length < 2 ? (
      <p className="muted">One snapshot so far. Run the pipeline on another day to draw the line between dates.</p>
    ) : null}
    </>
  );
}
