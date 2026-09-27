import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import App from "./App";

vi.stubGlobal(
  "fetch",
  vi.fn(async (input: RequestInfo) => {
    const url = String(input);
    if (url.includes("/runs/latest")) {
      return { ok: true, json: async () => null };
    }
    return { ok: true, json: async () => [] };
  }),
);

test("empty state names missing snapshot", async () => {
  render(
    <MemoryRouter initialEntries={["/movers"]}>
      <App />
    </MemoryRouter>,
  );
  expect(await screen.findByText(/second snapshot date/i)).toBeTruthy();
});
