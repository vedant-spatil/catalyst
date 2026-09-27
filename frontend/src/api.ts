const API = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:4000";

export async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API}${path}`);
  } catch {
    throw new Error("Unable to connect to the catalog API.");
  }
  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }
  return response.json() as Promise<T>;
}
