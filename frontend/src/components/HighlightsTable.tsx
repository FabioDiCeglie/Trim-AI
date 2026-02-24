import { useState } from "react";
import type { Overview } from "../types";

const HIGHLIGHTS_PREVIEW = 4;

export function HighlightsTable({
  highlights,
  totalSavings,
  currencyCode,
}: {
  highlights: Overview["highlights"];
  totalSavings: number;
  currencyCode: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const canCollapse = highlights.length > HIGHLIGHTS_PREVIEW;
  const visible = canCollapse && !expanded ? highlights.slice(0, HIGHLIGHTS_PREVIEW) : highlights;

  return (
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
            {visible.map((h, i) => (
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
          {totalSavings > 0 && (
            <tfoot>
              <tr className="border-t border-white/10 bg-white/5 font-medium">
                <td className="py-3 px-4 text-white" colSpan={3}>Total</td>
                <td className="py-3 px-4 text-right text-trim-green whitespace-nowrap">
                  ~{totalSavings.toFixed(1)} {currencyCode}/mo
                </td>
              </tr>
            </tfoot>
          )}
        </table>
        {canCollapse && (
          <button
            type="button"
            onClick={() => setExpanded((e) => !e)}
            className="w-full py-2.5 text-sm text-trim-muted hover:text-white transition-colors border-t border-white/10"
          >
            {expanded ? "Show less" : `Show all (${highlights.length})`}
          </button>
        )}
      </div>
    </section>
  );
}
