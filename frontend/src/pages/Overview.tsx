import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useConnection } from "../contexts/ConnectionContext";
import type { Overview as OverviewType, Project } from "../types";

export function Overview() {
  const { demo, selectedProjectId, setSelectedProjectId } = useConnection();

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ["projects", demo],
    queryFn: () => (demo ? api.demoProjects() : api.projects()),
  });

  const { data, isLoading, error } = useQuery<OverviewType>({
    queryKey: ["overview", selectedProjectId, demo],
    queryFn: () =>
      demo
        ? api.demoOverview(selectedProjectId)
        : api.overview(selectedProjectId ?? undefined),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-trim-green border-t-transparent animate-spin" />
          <p className="text-trim-muted">Loading overview…</p>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="rounded-2xl bg-red-500/10 border border-red-500/30 p-6">
        <p className="text-red-400 font-medium">Couldn’t load overview</p>
        <p className="text-trim-muted text-sm mt-1">{error instanceof Error ? error.message : "Something went wrong"}</p>
      </div>
    );
  }
  if (!data) return null;

  const { summary, highlights, billing } = data;
  const hasWaste = (summary?.waste_count ?? 0) > 0;
  const potentialSavings = billing?.potential_savings as { value?: number; currency?: string } | undefined;
  const topServices = (billing?.top_services as Array<{ service?: string; cost?: number }> | undefined) ?? [];
  const currencyCode = (billing?.currency_code as string) || "USD";

  const totalSavingsFromHighlights =
    highlights?.reduce((sum, h) => sum + (h.estimated_savings?.value ?? 0), 0) ?? 0;
  const totalCostFromServices = topServices.reduce(
    (sum, s) => sum + (s.cost != null ? Number(s.cost) : 0),
    0,
  );

  return (
    <div className="space-y-8 max-w-6xl mx-auto">

      <section className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Provider Overview</h1>
        {projects.length > 0 && (
          <label className="flex items-center gap-2">
            <span className="text-trim-muted text-sm whitespace-nowrap">Project</span>
            <div className="relative inline-flex">
              <select
                value={selectedProjectId ?? ""}
                onChange={(e) => setSelectedProjectId(e.target.value || null)}
                className="project-select appearance-none rounded-lg border border-white/10 text-sm py-2 pl-3 pr-7 focus:outline-none focus:ring-2 focus:ring-trim-green"
              >
                <option value="">All projects</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <svg className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-trim-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </label>
        )}
      </section>

      {!hasWaste && (!highlights || highlights.length === 0) && (
        <section className="rounded-2xl bg-trim-elevated p-8 text-center border border-white/10">
          <p className="text-trim-muted">No waste or highlights right now. Ask Trim for a summary.</p>
        </section>
      )}

      {/* What to fix — table */}
      {highlights && highlights.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">What to fix</h2>
          <div className="rounded-2xl bg-trim-elevated overflow-hidden border border-white/10">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-trim-muted font-medium">
                  <th className="py-3 px-4">Resource</th>
                  <th className="py-3 px-4">Issue</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4 text-right">Est. savings</th>
                </tr>
              </thead>
              <tbody>
                {highlights.map((h, i) => (
                  <tr key={`${h.id}-${i}`} className="border-b border-white/5 hover:bg-white/5">
                    <td className="py-3 px-4 font-medium text-white">{h.name}</td>
                    <td className="py-3 px-4 text-trim-muted">{h.reason}</td>
                    <td className="py-3 px-4 text-trim-muted">{h.recommended_action ?? "—"}</td>
                    <td className="py-3 px-4 text-right text-trim-green whitespace-nowrap">
                      {h.estimated_savings?.value != null
                        ? `~${h.estimated_savings.value} ${h.estimated_savings.currency}/mo`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
              {totalSavingsFromHighlights > 0 && (
                <tfoot>
                  <tr className="border-t border-white/10 bg-white/5 font-medium">
                    <td className="py-3 px-4 text-white" colSpan={3}>Total</td>
                    <td className="py-3 px-4 text-right text-trim-green whitespace-nowrap">
                      ~{totalSavingsFromHighlights.toFixed(1)} {currencyCode}/mo
                    </td>
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        </section>
      )}

      {/* Billing — table */}
      {(billing?.billing_account_display_name != null || potentialSavings?.value != null || topServices.length > 0) && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Billing</h2>
          <div className="rounded-2xl bg-trim-elevated p-5 border border-white/10">
            {(billing?.billing_account_display_name != null || (potentialSavings?.value != null && potentialSavings.value > 0)) && (
              <div className="mb-4 space-y-1">
                {billing?.billing_account_display_name != null && (
                  <p className="text-trim-muted text-sm">
                    Account: <span className="text-white">{String(billing.billing_account_display_name)}</span>
                    {billing?.currency_code != null && (
                      <span className="ml-2">({String(billing.currency_code)})</span>
                    )}
                  </p>
                )}
                {potentialSavings?.value != null && potentialSavings.value > 0 && (
                  <p className="text-trim-green font-medium">
                    Potential savings: {potentialSavings.value} {String(potentialSavings.currency ?? "")}
                  </p>
                )}
              </div>
            )}
            {topServices.length > 0 && (
              <div className="overflow-hidden rounded-lg border border-white/10">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-trim-muted font-medium">
                      <th className="py-2 px-3">Service</th>
                      <th className="py-2 px-3 text-right">Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topServices
                      .filter((s) => s.service != null && s.cost != null)
                      .map((s, i) => (
                        <tr key={`${s.service}-${i}`} className="border-b border-white/5">
                          <td className="py-2 px-3 text-white">{s.service}</td>
                          <td className="py-2 px-3 text-right text-trim-muted">
                            {currencyCode} {Number(s.cost).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                  {totalCostFromServices > 0 && (
                    <tfoot>
                      <tr className="border-t border-white/10 bg-white/5 font-medium">
                        <td className="py-2 px-3 text-white">Total</td>
                        <td className="py-2 px-3 text-right text-white">
                          {currencyCode} {totalCostFromServices.toFixed(2)}
                        </td>
                      </tr>
                    </tfoot>
                  )}
                </table>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
