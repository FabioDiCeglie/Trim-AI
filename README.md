# Trim 🔍

**Trim** is a cloud waste detection dashboard that surfaces overused, idle, and oversized resources across your cloud providers — starting with Google Cloud, then expanding to AWS, Azure, and Kubernetes.

Built on **Cloudflare Workers** (backend) + **React + Cloudflare Pages** (frontend).

---

## What It Detects

### Google Cloud (Phase 1)
| Category | What We Flag |
|---|---|
| Compute | Stopped VMs still charging for attached disks/IPs |
| Rightsizing | VMs with avg CPU < 5% or RAM < 10% over 7 days |
| Disks | Persistent disks not attached to any VM |
| Networking | Static external IPs reserved but unassigned |
| Cost | Top 5 most expensive services, month-over-month delta, daily spend anomalies (spike > 2× rolling avg) |

### AWS (Phase 2)
- EC2 idle/stopped instances, unattached EBS volumes, unused Elastic IPs
- CloudWatch CPU/RAM metrics for rightsizing
- Cost Explorer anomaly detection

### Azure (Phase 3)
- Idle VMs, unattached managed disks, unused public IPs
- Azure Monitor metrics, Cost Management API

### Kubernetes (Phase 4)
- Pods with no resource requests/limits
- Namespaces with no running workloads
- Oversized node pools vs actual usage

---

## Architecture

```
┌─────────────────────────────┐      ┌──────────────────────────────────────────────────────────────┐
│      Cloudflare Pages        │      │                     Cloudflare Worker                         │
│                              │      │                                                               │
│  React + Vite Dashboard      │      │  Router  /api/connect                                        │
│  - Onboarding                │      │          /api/:provider/projects                             │
│  - Overview                  ◄──────┤          /api/:provider/compute                              │
│  - Compute                   │      │          /api/:provider/metrics                              │
│  - Disks                     │      │          /api/:provider/billing                              │
│  - Network                   │      │                  │                                            │
│                              │      │                  ▼                                            │
└─────────────────────────────┘      │  ┌───────────────────────────────────────────────────────┐   │
                                      │  │           Abstract Provider Interface                  │   │
                                      │  │                                                        │   │
                                      │  │  interface CloudProvider {                             │   │
                                      │  │    getProjects()     → Project[]                       │   │
                                      │  │    getCompute()      → Resource[]                      │   │
                                      │  │    getMetrics()      → Metric[]                        │   │
                                      │  │    getBilling()      → CostReport                      │   │
                                      │  │  }                                                     │   │
                                      │  │                                                        │   │
                                      │  │   ┌──────────┐  ┌──────────┐  ┌───────┐  ┌────────┐  │   │
                                      │  │   │  GCP ✅  │  │  AWS 🔜  │  │Azure  │  │  K8s   │  │   │
                                      │  │   └────┬─────┘  └────┬─────┘  └───┬───┘  └───┬────┘  │   │
                                      │  └────────┼─────────────┼────────────┼───────────┼───────┘   │
                                      │           │             │            │           │            │
                                      │  ┌────────▼─────────────▼────────────▼───────────▼────────┐  │
                                      │  │              Normalized Types (types.ts)                │  │
                                      │  │  Resource { id, name, provider, region, type,          │  │
                                      │  │             monthlyCost, wasteReason, metrics }         │  │
                                      │  └────────────────────────────────────────────────────────┘  │
                                      │                         │                                     │
                                      │              ┌──────────▼──────────┐                         │
                                      │              │   Cloudflare KV      │                         │
                                      │              │  (credentials store) │                         │
                                      │              └─────────────────────┘                         │
                                      └──────────────────────────────────────────────────────────────┘
                                                               │
                              ┌────────────────────────────────▼─────────────────────────────────┐
                              │                          Cloud Provider APIs                       │
                              │  GCP: Compute Engine · Cloud Monitoring · Billing · Resource Mgr  │
                              │  AWS: EC2 · CloudWatch · Cost Explorer · EBS                      │
                              │  Azure: Compute · Monitor · Cost Management                       │
                              │  K8s: Metrics Server · kube-api                                   │
                              └──────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Cloudflare Workers (TypeScript) |
| Credential storage | Cloudflare KV |
| Frontend | React 18 + Vite + TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| Charts | Recharts |
| Data fetching | React Query |
| Deployment | Cloudflare Pages (frontend) + Wrangler (worker) |

---

## Project Structure

```
trim/
├── README.md
├── worker/                              # Cloudflare Worker
│   ├── src/
│   │   ├── index.ts                     # Router entry point + CORS
│   │   ├── types.ts                     # Normalized cross-provider types
│   │   │                                #   Resource, Metric, CostReport, WasteReason
│   │   ├── provider.interface.ts        # CloudProvider interface all adapters must implement
│   │   │                                #   getProjects() / getCompute() / getMetrics() / getBilling()
│   │   ├── registry.ts                  # Maps provider name → adapter (loaded from KV creds)
│   │   └── providers/
│   │       ├── gcp/                     # ✅ Phase 1
│   │       │   ├── index.ts             # GCPProvider implements CloudProvider
│   │       │   ├── auth.ts              # Service Account JWT signing (Web Crypto API)
│   │       │   ├── compute.ts           # Compute Engine: VMs, disks, static IPs
│   │       │   ├── monitoring.ts        # Cloud Monitoring: CPU / RAM time-series
│   │       │   └── billing.ts           # Billing API: cost breakdown + anomaly detection
│   │       ├── aws/                     # 🔜 Phase 2
│   │       │   ├── index.ts             # AWSProvider implements CloudProvider
│   │       │   ├── auth.ts              # AWS Signature v4 signing
│   │       │   ├── ec2.ts
│   │       │   ├── cloudwatch.ts
│   │       │   └── cost-explorer.ts
│   │       ├── azure/                   # 🔜 Phase 3
│   │       │   └── index.ts             # AzureProvider implements CloudProvider
│   │       └── k8s/                     # 🔜 Phase 4
│   │           └── index.ts             # K8sProvider implements CloudProvider
│   ├── wrangler.toml
│   └── package.json
└── dashboard/                           # React App
    ├── src/
    │   ├── App.tsx
    │   ├── types.ts                     # Mirrors worker normalized types on the frontend
    │   ├── pages/
    │   │   ├── Onboarding.tsx           # Multi-provider connect flow (GCP JSON, AWS keys, etc.)
    │   │   ├── Overview.tsx             # Cross-provider waste score + cost chart + top issues
    │   │   ├── Compute.tsx              # Unified VM/instance table with CPU/RAM heatmap
    │   │   ├── Disks.tsx                # Unattached volumes/disks across providers
    │   │   └── Network.tsx              # Unused IPs / load balancers across providers
    │   ├── components/
    │   │   ├── ProviderBadge.tsx        # GCP / AWS / Azure / K8s colored badge
    │   │   ├── ResourceCard.tsx
    │   │   ├── WasteScore.tsx
    │   │   └── charts/
    │   └── hooks/
    │       └── useProvider.ts           # Generic hook — useProvider('gcp') / useProvider('aws')
    ├── package.json
    └── vite.config.ts
```

---

## Roadmap

- [x] Plan & architecture
- [ ] **Foundation — Abstract Provider Layer**
  - [ ] Define `CloudProvider` interface (`provider.interface.ts`)
  - [ ] Define normalized `Resource`, `Metric`, `CostReport`, `WasteReason` types (`types.ts`)
  - [ ] Build `registry.ts` to map provider name → adapter instance
  - [ ] Provider-agnostic router: `/api/:provider/compute`, `/api/:provider/metrics`, `/api/:provider/billing`
- [ ] **Phase 1 — GCP**
  - [ ] Scaffold monorepo (`worker/` + `dashboard/`)
  - [ ] `GCPProvider implements CloudProvider`
  - [ ] GCP Service Account JWT signing via Web Crypto API
  - [ ] `POST /api/connect` — save credentials to KV
  - [ ] `GET /api/gcp/projects` — list accessible projects
  - [ ] `GET /api/gcp/compute` — idle VMs, unattached disks, unused IPs
  - [ ] `GET /api/gcp/metrics` — CPU/RAM time-series
  - [ ] `GET /api/gcp/billing` — cost breakdown + anomalies
  - [ ] Onboarding Step 1 — provider selector UI (GCP / AWS / Azure / K8s cards)
  - [ ] Onboarding Step 2 — provider-specific credential form (GCP JSON upload, AWS keys, etc.)
  - [ ] Onboarding Step 3 — project selector after successful connection
  - [ ] `POST /api/connect` — validate, AES-GCM encrypt creds, store in KV, return `connectionId`
  - [ ] `GET /api/:provider/projects` — decrypt creds from KV, call provider, return project list
  - [ ] Overview page — all services grid, waste score, cost chart, wasteful resources highlighted in red
  - [ ] Compute page — full VM/instance table, idle/oversized rows in red with waste reason tooltip
  - [ ] Disks page — all disks listed, unattached ones in red
  - [ ] Network page — all IPs / load balancers listed, unused ones in red
  - [ ] Cloudflare Pages + Worker deployment config
  - [ ] `wrangler secret put ENCRYPTION_KEY` setup in deployment docs
- [ ] **Phase 2 — AWS**
  - [ ] AWS provider module (EC2, EBS, Elastic IPs, CloudWatch)
  - [ ] AWS IAM access key onboarding
  - [ ] Unified dashboard view across GCP + AWS
- [ ] **Phase 3 — Azure**
  - [ ] Azure provider module (VMs, Managed Disks, Public IPs, Cost Management)
  - [ ] Azure Service Principal onboarding
- [ ] **Phase 4 — Kubernetes**
  - [ ] K8s provider module (pods, namespaces, node pools)
  - [ ] kubeconfig / in-cluster auth

---

## Getting Started (once scaffold is ready)

```bash
# Worker
cd worker
npm install
wrangler kv:namespace create CREDENTIALS
wrangler dev

# Dashboard
cd dashboard
npm install
npm run dev
```

## Dashboard UI

Every page follows the same principle: **show all resources, surface the waste in red.**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Overview                                             [GCP] [AWS]   │
│                                                                     │
│  Waste Score: 74/100   Est. monthly waste: $340                     │
│  ████████████████░░░░  ← colored bar (green → red)                 │
│                                                                     │
│  All Services                                                        │
│  ┌──────────────┬────────────┬───────────┬────────────────────────┐ │
│  │ Service       │ Resources  │ Cost/mo   │ Status                 │ │
│  ├──────────────┼────────────┼───────────┼────────────────────────┤ │
│  │ Compute       │ 12 VMs     │ $210      │ ● 3 idle               │ │  ← red row
│  │ Disks         │ 8 volumes  │ $45       │ ● 5 unattached         │ │  ← red row
│  │ Networking    │ 6 IPs      │ $18       │ ● 4 unused             │ │  ← red row
│  │ Cloud Storage │ 14 buckets │ $62       │ ✓ All in use           │ │  ← green
│  │ Cloud SQL     │ 2 DBs      │ $120      │ ✓ All in use           │ │  ← green
│  └──────────────┴────────────┴───────────┴────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Compute                                                            │
│                                                                     │
│  ┌──────────────┬──────────┬───────┬───────┬───────────────────┐   │
│  │ Instance      │ Region   │ CPU   │ RAM   │ Issue             │   │
│  ├──────────────┼──────────┼───────┼───────┼───────────────────┤   │
│  │ prod-api-01   │ us-east1 │  62%  │  55%  │ ✓ Healthy         │   │
│  │ prod-api-02   │ us-east1 │  58%  │  49%  │ ✓ Healthy         │   │
│  │ staging-01    │ us-east1 │   2%  │   4%  │ ● Idle — stopped  │   │  ← red
│  │ old-worker    │ eu-west1 │   1%  │   3%  │ ● Oversized (n2)  │   │  ← red
│  │ test-db       │ us-east1 │   0%  │   0%  │ ● Not running     │   │  ← red
│  └──────────────┴──────────┴───────┴───────┴───────────────────┘   │
│                                                                     │
│  Hover/click a red row → waste reason + recommended action tooltip  │
└─────────────────────────────────────────────────────────────────────┘
```

**Color logic:**
| State | Color | Condition |
|---|---|---|
| Healthy | Green | Resource active, CPU > 5%, RAM > 10%, cost justified |
| Warning | Amber | CPU 5–15% — undersized or slightly idle |
| Waste | Red | Idle, stopped, unattached, unused, or 0% utilization |

Each red row shows a **waste reason badge** (e.g. "Idle 7d", "Unattached", "Unused IP", "Oversized") and on hover a tooltip with the recommended action ("Delete", "Downsize to n2-small", "Release IP").

---

## Onboarding Flow

The connection flow is provider-agnostic and built into the dashboard:

```
┌─────────────────────────────────────────────────────────────┐
│                     Onboarding — Step 1                      │
│                                                             │
│   Choose your cloud provider:                               │
│                                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │   GCP    │  │   AWS    │  │  Azure   │  │  K8s     │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Onboarding — Step 2 (provider-specific)         │
│                                                             │
│  GCP:    Upload / paste Service Account JSON                │
│  AWS:    Access Key ID + Secret Access Key + Region         │
│  Azure:  Tenant ID + Client ID + Client Secret              │
│  K8s:    Paste kubeconfig or in-cluster token               │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼  POST /api/connect
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Worker                         │
│                                                             │
│  1. Validate credentials shape                              │
│  2. Encrypt payload with AES-GCM (Web Crypto API)           │
│     using a secret key stored as a Worker Secret            │
│  3. Store encrypted blob in KV under a connectionId         │
│  4. Return { connectionId } to the frontend                 │
│                                                             │
│  connectionId saved in localStorage — used on every         │
│  subsequent API call as a bearer token                      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Onboarding — Step 3: Select Project            │
│                                                             │
│  GET /api/:provider/projects  (worker decrypts creds,       │
│  calls provider API, returns project / account list)        │
│                                                             │
│  User picks which project(s) to monitor → Dashboard         │
└─────────────────────────────────────────────────────────────┘
```

**Encryption detail:**
- A `ENCRYPTION_KEY` Worker Secret (32-byte AES-GCM key) is set once via `wrangler secret put`
- The Worker never stores plaintext credentials — only the AES-GCM encrypted blob + IV in KV
- The frontend only ever holds the `connectionId` (a UUID), never the raw credentials

---

### GCP — Required Service Account Roles

| Role | Why |
|---|---|
| `Compute Viewer` | List VMs, disks, static IPs |
| `Monitoring Viewer` | CPU / RAM metrics |
| `Billing Account Viewer` | Cost data + anomalies |
| `Project Viewer` | List projects |

---

## Multi-Cloud Design Principle

The Worker is built provider-agnostic from day one. Each cloud provider lives in `worker/src/providers/<provider>/` and implements the shared `CloudProvider` interface. The router, KV storage, and encryption layer are completely provider-unaware — adding AWS/Azure is a drop-in module with zero changes to the core.
# Trim-AI
