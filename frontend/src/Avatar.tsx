type Props = { src: string | null | undefined; name: string };

export default function Avatar({ src, name }: Props) {
  if (src) {
    return <img className="avatar" src={src} alt="" />;
  }
  const letter = (name || "?").trim().charAt(0).toUpperCase();
  return <span className="avatar placeholder">{letter}</span>;
}
