type Props = { title: string; description: string };

export default function EmptyState({ title, description }: Props) {
  return (
    <section className="empty">
      <h2>{title}</h2>
      <p>{description}</p>
    </section>
  );
}
