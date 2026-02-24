import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useConnection } from "../contexts/ConnectionContext";

const PROVIDERS = [
  { value: "gcp", label: "Google Cloud (GCP)", enabled: true },
  { value: "aws", label: "Amazon Web Services (AWS)", enabled: false },
  { value: "azure", label: "Microsoft Azure", enabled: false },
  { value: "k8s", label: "Kubernetes (K8s)", enabled: false },
] as const;

type Provider = (typeof PROVIDERS)[number]["value"];

export function Onboarding() {
  const navigate = useNavigate();
  const { setConnection, enterDemo } = useConnection();
  const [provider, setProvider] = useState<Provider>("gcp");
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
              <h2 className="font-medium text-white mb-2">1. Create a service account</h2>
              <ol className="list-decimal list-inside space-y-1.5 text-trim-muted">
                <li>In <strong className="text-white">Google Cloud Console</strong>, select the project you want Trim to analyze.</li>
                <li>Go to <strong className="text-white">IAM &amp; Admin → Service Accounts</strong>. Create a service account (or use an existing one).</li>
                <li>Grant it these roles: <strong className="text-white">Compute Viewer</strong>, <strong className="text-white">Monitoring Viewer</strong>, <strong className="text-white">Billing Account Viewer</strong>, <strong className="text-white">Project Viewer</strong>.</li>
              </ol>
            </div>
            <div>
              <h2 className="font-medium text-white mb-2">2. Set up billing (before creating the key)</h2>
              <ol className="list-decimal list-inside space-y-1.5 text-trim-muted">
                <li><strong className="text-white">Link a billing account:</strong> Go to <strong className="text-white">Billing</strong> in the console → <strong className="text-white">Link a billing account</strong> to your project. Trim needs this to show account name and currency.</li>
                <li><strong className="text-white">Cost breakdown &amp; potential savings (optional):</strong> Go to <strong className="text-white">Billing → Billing export</strong>. Create a BigQuery dataset for the export. Grant your service account <strong className="text-white">BigQuery Data Viewer</strong> (and <strong className="text-white">Job User</strong> if the dataset is in another project) on that dataset. You’ll add the dataset ID to the JSON in step 4.</li>
              </ol>
            </div>
            <div>
              <h2 className="font-medium text-white mb-2">3. Create key and paste into Trim</h2>
              <ol className="list-decimal list-inside space-y-1.5 text-trim-muted">
                <li>Back in <strong className="text-white">Service Accounts</strong>, open your account → <strong className="text-white">Keys</strong> → <strong className="text-white">Add key → Create new key → JSON</strong>. Download the file.</li>
                <li>If you use BigQuery billing export, add to the JSON: <code className="bg-white/10 px-1 rounded">billing_export_dataset_id</code>. If the dataset is in another project, add <code className="bg-white/10 px-1 rounded">billing_export_project_id</code>. For per-resource savings use <code className="bg-white/10 px-1 rounded">billing_export_use_detailed: true</code> (requires detailed export).</li>
                <li>Paste the entire JSON in the box on the right (must include <code className="bg-white/10 px-1 rounded">type</code>, <code className="bg-white/10 px-1 rounded">project_id</code>, <code className="bg-white/10 px-1 rounded">private_key</code>, <code className="bg-white/10 px-1 rounded">client_email</code>), then click Connect.</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Right: form */}
        <div>
          <label className="block text-trim-muted text-sm mb-2">Provider</label>
          <select
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value as Provider);
              setJson("");
              setError("");
            }}
            className="w-full mb-5 py-2.5 pl-3 pr-8 rounded-xl bg-white border border-white/20 text-black text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value} disabled={!p.enabled}>
                {p.label}{!p.enabled ? " (coming soon)" : ""}
              </option>
            ))}
          </select>
          <p className="text-trim-muted text-sm mb-2">Credentials (JSON)</p>
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
          <div className="mt-4 flex items-center gap-3">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-trim-muted text-xs">or</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>
          <button
            type="button"
            onClick={() => {
              enterDemo();
              navigate("/overview", { replace: true });
            }}
            disabled={loading}
            className="mt-4 w-full py-3 px-4 border border-white/20 text-white font-semibold rounded-full hover:bg-white/10 transition-colors disabled:opacity-50 disabled:pointer-events-none"
          >
            Try Demo
          </button>
        </div>
      </div>
    </div>
  );
}
