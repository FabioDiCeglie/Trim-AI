import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useConnection } from "../contexts/ConnectionContext";

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
    <div className="min-h-screen flex items-center justify-center p-6 bg-trim-base">
      <div className="w-full max-w-md">
        <h1 className="text-xl font-medium text-white mb-6">
          Connect to your cloud
        </h1>
        <p className="text-trim-muted text-sm mb-4">
          Paste your GCP service account JSON (project_id, private_key, client_email).
        </p>
        <textarea
          value={json}
          onChange={(e) => setJson(e.target.value)}
          placeholder='{"type":"service_account","project_id":"..."}'
          className="w-full h-40 p-4 rounded-xl bg-white border border-white/20 text-black placeholder:text-gray-400 font-mono text-sm resize-y focus:outline-none focus:ring-2 focus:ring-white/50"
          spellCheck={false}
        />
        {error && (
          <p className="mt-3 text-sm text-red-400">{error}</p>
        )}
        <button
          type="button"
          onClick={handleConnect}
          disabled={loading || !json.trim()}
          className="mt-6 w-full py-3 px-4 bg-white text-black font-semibold rounded-full hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:pointer-events-none"
        >
          {loading ? "Connecting…" : "Connect"}
        </button>
      </div>
    </div>
  );
}
