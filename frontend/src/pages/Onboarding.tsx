import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useConnection } from "../hooks/useConnection";

export function Onboarding() {
  const navigate = useNavigate();
  const { setConnection } = useConnection();
  const [provider] = useState<"gcp">("gcp");
  const [json, setJson] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleConnect() {
    setError("");
    setLoading(true);
    try {
      const credentials = JSON.parse(json) as Record<string, unknown>;
      const { connectionId, provider: p } = await api.connect(provider, credentials);
      setConnection(connectionId, p);
      navigate("/overview", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto mt-12">
      <h1 className="text-2xl font-semibold text-slate-800 mb-2">
        Connect your cloud
      </h1>
      <p className="text-slate-600 mb-6">
        Paste your GCP service account JSON (project_id, private_key, client_email).
      </p>
      <textarea
        value={json}
        onChange={(e) => setJson(e.target.value)}
        placeholder='{"type":"service_account","project_id":"..."}'
        className="w-full h-40 p-3 rounded-lg border border-slate-300 font-mono text-sm resize-y"
        spellCheck={false}
      />
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
      <button
        type="button"
        onClick={handleConnect}
        disabled={loading || !json.trim()}
        className="mt-4 px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:pointer-events-none"
      >
        {loading ? "Connecting…" : "Connect"}
      </button>
    </div>
  );
}
