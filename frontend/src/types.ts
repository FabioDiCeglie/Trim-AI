export type Provider = "gcp" | "aws" | "azure" | "k8s";

export interface ConnectResponse {
  connectionId: string;
  provider: Provider;
}

export interface Overview {
  summary: {
    total_resources: number;
    waste_count: number;
    with_metrics: number;
    over_provisioned: number;
    under_provisioned: number;
  };
  summary_cards: Array<{
    id: string;
    label: string;
    value: string | number;
    sublabel?: string;
  }>;
  highlights: Array<{
    type: string;
    resource_type: string;
    id: string;
    name: string;
    reason: string;
    status?: string;
    recommended_action?: string;
    estimated_savings?: { value: number; currency: string };
  }>;
  compute: Array<Record<string, unknown>>;
  metrics: Array<Record<string, unknown>>;
  billing: Record<string, unknown>;
}

export interface ChatResponse {
  reply: string;
}
