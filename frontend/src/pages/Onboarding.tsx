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
    <div className="min-h-screen flex items-center p-6 bg-trim-base">
      <div className="w-full max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 md:gap-12 items-start">
        {/* Left: instructions */}
        <div>
          <h1 className="text-xl font-medium text-white mb-6 text-left">
            Connect to your cloud
          </h1>
          <div className="rounded-xl bg-white/5 border border-white/10 p-5 space-y-5 text-sm">
            <div>
              <h2 className="font-medium text-white mb-2">1. Get GCP credentials (step by step)</h2>
              <ol className="list-decimal list-inside space-y-1.5 text-trim-muted">
                <li>In Google Cloud Console, go to <strong className="text-white">IAM & Admin → Service Accounts</strong>.</li>
                <li>Create a service account (or pick an existing one) in the project you want Trim to analyze.</li>
                <li>Grant these roles: <strong className="text-white">Compute Viewer</strong>, <strong className="text-white">Monitoring Viewer</strong>, <strong className="text-white">Billing Account Viewer</strong>, <strong className="text-white">Project Viewer</strong>.</li>
                <li>Open the service account → <strong className="text-white">Keys</strong> → Add key → Create new key → <strong className="text-white">JSON</strong>. Download the file.</li>
                <li>Paste the entire JSON in the box on the right (must include <code className="bg-white/10 px-1 rounded">type</code>, <code className="bg-white/10 px-1 rounded">project_id</code>, <code className="bg-white/10 px-1 rounded">private_key</code>, <code className="bg-white/10 px-1 rounded">client_email</code>).</li>
              </ol>
            </div>
            <div>
              <h2 className="font-medium text-white mb-2">2. Set up billing</h2>
              <ol className="list-decimal list-inside space-y-1.5 text-trim-muted">
                <li><strong className="text-white">Link a billing account:</strong> In GCP go to <strong className="text-white">Billing</strong> → select your project → Link a billing account. Trim needs this to show account name and currency.</li>
                <li><strong className="text-white">Cost breakdown &amp; potential savings (optional):</strong> Enable <strong className="text-white">BigQuery billing export</strong> (Billing → Billing export), create a dataset, give your service account <strong className="text-white">BigQuery Data Viewer</strong> on it. Then add to your JSON: <code className="bg-white/10 px-1 rounded">billing_export_dataset_id</code>. If the dataset is in another project, add <code className="bg-white/10 px-1 rounded">billing_export_project_id</code>. For per-resource savings set <code className="bg-white/10 px-1 rounded">billing_export_use_detailed</code> to <code className="bg-white/10 px-1 rounded">true</code>.</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Right: form */}
        <div>
          <p className="text-trim-muted text-sm mb-2">Service account JSON</p>
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
    </div>
  );
}
