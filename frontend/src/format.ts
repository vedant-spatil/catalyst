const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "Unknown";
  const part = iso.slice(0, 10);
  const bits = part.split("-");
  if (bits.length !== 3) return part;
  const year = Number(bits[0]);
  const month = Number(bits[1]);
  const day = Number(bits[2]);
  if (!year || !month || !day) return part;
  return `${day} ${MONTHS[month - 1]} ${year}`;
}

export function weekLabel(year: number, week: number): string {
  return `W${week}`;
}
