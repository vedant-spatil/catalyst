import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { getJson } from "./api";
import { formatDate } from "./format";
import type { RunLog } from "./types";
import PipelineGuide from "./PipelineGuide";
import Exposure from "./views/Exposure";
import Movers from "./views/Movers";
import ReleaseCurve from "./views/ReleaseCurve";
import Weekly from "./views/Weekly";

export default function App() {
  const [run, setRun] = useState<RunLog | null | undefined>(undefined);

  useEffect(() => {
    getJson<RunLog | null>("/runs/latest")
      .then(setRun)
      .catch(() => setRun(null));
  }, []);

  const runDate = run?.snapshot_date || run?.finished_at || run?.started_at;
  const ok = run?.status === "success";

  return (
    <div className="app">
      <header className="top">
        <h1>Catalyst</h1>
        <nav>
          <NavLink to="/exposure">Exposure</NavLink>
          <NavLink to="/release-curve">Release Curve</NavLink>
          <NavLink to="/movers">Movers</NavLink>
          <NavLink to="/weekly">Weekly</NavLink>
        </nav>
        <div className={`last-run ${ok ? "ok" : ""}`}>
          <span className="dot" />
          <div>
            <small>Last run</small>
            <strong>{runDate ? formatDate(runDate) : "No pipeline run yet"}</strong>
          </div>
        </div>
      </header>
      <PipelineGuide key={run === undefined ? "loading" : ok ? "ran" : "empty"} startOpen={run !== undefined && !ok} />
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/exposure" replace />} />
          <Route path="/exposure" element={<Exposure />} />
          <Route path="/release-curve" element={<ReleaseCurve />} />
          <Route path="/movers" element={<Movers />} />
          <Route path="/weekly" element={<Weekly />} />
        </Routes>
      </main>
    </div>
  );
}
