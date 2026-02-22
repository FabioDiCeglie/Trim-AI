import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Overview as OverviewType } from "../types";

export function Overview() {
  const { data, isLoading, error } = useQuery<OverviewType>({
    queryKey: ["overview"],
    queryFn: () => api.overview(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-trim-green border-t-transparent animate-spin" />
          <p className="text-trim-muted">Loading dashboard…</p>
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

  const { summary, summary_cards, highlights, billing } = data;
  const hasWaste = (summary?.waste_count ?? 0) > 0;
  const potentialSavings = billing?.potential_savings as { value?: number; currency?: string } | undefined;

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Header */}
      <section>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-trim-muted mt-1">
          {hasWaste ? "You have items that need attention." : "Your cloud looks healthy."}
        </p>
      </section>

      {/* Stats row */}
      <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {summary_cards.map((card) => {
          const isHighlight = card.id === "waste_count" && Number(card.value) > 0;
          const isSavings = card.id === "potential_savings";
          return (
            <div
              key={card.id}
              className={`rounded-2xl p-5 transition-colors ${
                isHighlight ? "bg-amber-500/10 border border-amber-500/30" : "bg-trim-elevated"
              } ${isSavings && card.value ? "bg-trim-green/10 border border-trim-green/30" : ""}`}
            >
              <p className="text-trim-muted text-xs font-medium uppercase tracking-wider">
                {card.label}
              </p>
              <p className={`mt-2 text-2xl font-bold ${isHighlight ? "text-amber-400" : isSavings ? "text-trim-green" : "text-white"}`}>
                {typeof card.value === "number" ? card.value : card.value}
              </p>
              {card.sublabel && (
                <p className="text-trim-muted text-xs mt-1">{card.sublabel}</p>
              )}
            </div>
          );
        })}
      </section>

      {/* Focus / What to fix */}
      {highlights && highlights.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">What to fix</h2>
          <div className="rounded-2xl bg-trim-elevated overflow-hidden">
            <ul className="divide-y divide-white/10">
              {highlights.map((h, i) => (
                <li key={`${h.id}-${h.reason}-${i}`} className="p-4 md:p-5 hover:bg-white/5 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <span className="font-medium text-white">{h.name}</span>
                      <span className="text-trim-muted mx-2">·</span>
                      <span className="text-amber-400/90 text-sm">{h.reason}</span>
                      {h.estimated_savings?.value != null && (
                        <span className="text-trim-green text-sm ml-2">
                          ~{h.estimated_savings.value} {h.estimated_savings.currency}/mo
                        </span>
                      )}
                    </div>
                  </div>
                  {h.recommended_action && (
                    <p className="text-trim-muted text-sm mt-2">{h.recommended_action}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* At a glance / Billing */}
      {(billing?.billing_account_display_name || potentialSavings?.value) && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Billing</h2>
          <div className="rounded-2xl bg-trim-elevated p-5">
            {billing?.billing_account_display_name && (
              <p className="text-trim-muted text-sm">
                Account: <span className="text-white">{billing.billing_account_display_name}</span>
                {billing?.currency_code && (
                  <span className="ml-2">({billing.currency_code})</span>
                )}
              </p>
            )}
            {potentialSavings?.value != null && potentialSavings.value > 0 && (
              <p className="text-trim-green font-medium mt-2">
                Potential savings: {potentialSavings.value} {potentialSavings.currency}
              </p>
            )}
          </div>
        </section>
      )}

      {!hasWaste && (!highlights || highlights.length === 0) && (
        <section className="rounded-2xl bg-trim-elevated p-8 text-center">
          <p className="text-trim-muted">No waste or highlights right now. Ask Trim for a summary.</p>
        </section>
      )}
    </div>
  );
}
