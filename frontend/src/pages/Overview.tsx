import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Overview } from "../types";

export function Overview() {
  const { data, isLoading, error } = useQuery<Overview>({
    queryKey: ["overview"],
    queryFn: () => api.overview(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-slate-500">Loading overview…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-4">
        <p className="text-red-800">{error instanceof Error ? error.message : "Failed to load overview"}</p>
      </div>
    );
  }
  if (!data) return null;

  const { summary_cards, highlights } = data;

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-slate-800">Overview</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {summary_cards.map((card) => (
          <div
            key={card.id}
            className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm"
          >
            <p className="text-sm text-slate-500">{card.label}</p>
            <p className="text-xl font-semibold text-slate-800 mt-1">{card.value}</p>
            {card.sublabel && (
              <p className="text-xs text-slate-400 mt-0.5">{card.sublabel}</p>
            )}
          </div>
        ))}
      </div>

      {highlights.length > 0 && (
        <section>
          <h2 className="text-lg font-medium text-slate-800 mb-3">Highlights</h2>
          <ul className="space-y-2">
            {highlights.map((h) => (
              <li
                key={`${h.id}-${h.reason}`}
                className="bg-amber-50 border border-amber-200 rounded-lg p-3"
              >
                <span className="font-medium text-slate-800">{h.name}</span>
                <span className="text-slate-600"> — {h.reason}</span>
                {h.estimated_savings?.value && (
                  <span className="text-slate-500 text-sm ml-2">
                    (~{h.estimated_savings.value} {h.estimated_savings.currency}/mo)
                  </span>
                )}
                {h.recommended_action && (
                  <p className="text-sm text-slate-600 mt-1">{h.recommended_action}</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
