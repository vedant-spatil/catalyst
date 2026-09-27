import type { ReactNode } from "react";

type Props = { eyebrow: string; title: string; description: string; extra?: ReactNode };

export default function PageIntro({ eyebrow, title, description, extra }: Props) {
  return (
    <div className="page-intro">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="page-title">{title}</h2>
        <p className="lede">{description}</p>
      </div>
      {extra}
    </div>
  );
}
