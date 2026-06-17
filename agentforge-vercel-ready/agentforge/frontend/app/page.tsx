"use client";

import { useState } from "react";

export default function Home() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runSprint() {
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description }),
      });

      if (!res.ok) throw new Error(`Request failed: ${res.status}`);

      const data = await res.json();
      setResult(data.outputs || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong calling the API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 30 }}>
      <h1>AgentForge</h1>

      <input
        placeholder="Sprint title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <br /><br />

      <textarea
        rows={6}
        cols={60}
        placeholder="Describe your project"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />

      <br /><br />

      <button onClick={runSprint} disabled={loading}>
        {loading ? "Running..." : "Run Sprint"}
      </button>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      <hr />

      {result.map((r, i) => (
        <div key={i}>
          <h3>{r.role}</h3>
          <p>{r.summary}</p>
        </div>
      ))}
    </main>
  );
}
