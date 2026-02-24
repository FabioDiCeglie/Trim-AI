OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Trim API",
        "description": "Cloud waste detection engine — surfaces idle, oversized, and unused resources across cloud providers.",
        "version": "0.1.0",
    },
    "tags": [
        {"name": "Health", "description": "Service health"},
        {"name": "Connect", "description": "Provider credential management"},
        {"name": "Providers", "description": "Cloud provider data endpoints"},
        {"name": "Demo", "description": "Try-it-out endpoints — no authentication required"},
    ],
    "paths": {
        "/api/v1/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Health check",
                "operationId": "health",
                "responses": {
                    "204": {"description": "Service is healthy"}
                },
            }
        },
        "/api/v1/connect": {
            "post": {
                "tags": ["Connect"],
                "summary": "Connect a cloud provider",
                "description": (
                    "Validates, AES-GCM encrypts, and stores provider credentials in KV. "
                    "Returns a `connectionId` (UUID) the frontend uses on all subsequent requests. "
                    "Raw credentials are never stored — only the encrypted blob."
                ),
                "operationId": "connect",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ConnectRequest"},
                            "examples": {
                                "gcp": {
                                    "summary": "Google Cloud",
                                    "value": {
                                        "provider": "gcp",
                                        "credentials": {
                                            "type": "service_account",
                                            "project_id": "my-project",
                                            "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...",
                                            "client_email": "sa@my-project.iam.gserviceaccount.com",
                                        },
                                    },
                                },
                                "aws": {
                                    "summary": "Amazon Web Services",
                                    "value": {
                                        "provider": "aws",
                                        "credentials": {
                                            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                                            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                                            "region": "us-east-1",
                                        },
                                    },
                                },
                            },
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Credentials stored — connection established",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ConnectResponse"},
                                "example": {
                                    "connectionId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                                    "provider": "gcp",
                                },
                            }
                        },
                    },
                    "400": {
                        "description": "Invalid provider or missing credential fields",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
            }
        },
        "/api/v1/chat": {
            "post": {
                "tags": ["Providers"],
                "summary": "AI chat",
                "description": "Ask Trim anything about your cloud waste and costs. Uses the connection from Authorization header (any provider). Fetches fresh overview data and returns an AI-generated reply.",
                "operationId": "chat",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["message"],
                                "properties": {
                                    "message": {"type": "string", "description": "User question"},
                                    "demo": {"type": "boolean", "description": "When true, skip auth and use mock overview data as AI context", "default": False},
                                    "project": {"type": "string", "description": "Demo project ID (only used when demo=true). Omit for all-projects context."},
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "AI reply",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "properties": {"reply": {"type": "string"}}},
                            }
                        },
                    },
                    "401": {"description": "Missing or invalid Authorization header", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                    "502": {"description": "AI error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                    "503": {"description": "AI not configured", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            }
        },
        "/api/v1/{provider}/projects": {
            "get": {
                "tags": ["Providers"],
                "summary": "List projects",
                "description": "List accessible projects/accounts for the connected provider.",
                "operationId": "getProjects",
                "parameters": [
                    {
                        "name": "provider",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "enum": ["gcp", "aws", "azure", "k8s"]},
                    }
                ],
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "List of projects",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Project"}},
                                "example": [
                                    {"id": "happycustomersai", "name": "HappyCustomersAI", "provider": "gcp"}
                                ],
                            }
                        },
                    },
                    "401": {"description": "Missing or invalid Authorization header", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            }
        },
        "/api/v1/{provider}/compute": {
            "get": {
                "tags": ["Providers"],
                "summary": "List compute resources",
                "description": "Return VMs, disks, and IPs — flagging idle, stopped, unattached, or oversized ones.",
                "operationId": "getCompute",
                "parameters": [
                    {
                        "name": "provider",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "enum": ["gcp", "aws", "azure", "k8s"]},
                    }
                ],
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "List of compute resources",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Resource"}},
                            }
                        },
                    },
                    "401": {"description": "Missing or invalid Authorization header", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            }
        },
        "/api/v1/{provider}/metrics": {
            "get": {
                "tags": ["Providers"],
                "summary": "Get resource metrics",
                "description": "Return CPU / RAM time-series for compute resources (e.g. GCE VMs). Optional query: days=30 (default) or 1–30.",
                "operationId": "getMetrics",
                "parameters": [
                    {
                        "name": "provider",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "enum": ["gcp", "aws", "azure", "k8s"]},
                    },
                    {
                        "name": "days",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "minimum": 1, "maximum": 30, "default": 30},
                        "description": "Number of days of metrics to return (1–30).",
                    },
                ],
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "List of metrics",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Metric"}},
                            }
                        },
                    },
                    "401": {"description": "Missing or invalid Authorization header", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            }
        },
        "/api/v1/{provider}/overview": {
            "get": {
                "tags": ["Providers"],
                "summary": "Dashboard overview",
                "description": "Dashboard payload: summary, summary_cards (for top row), highlights (waste + utilization alerts), compute, metrics (avg/peak CPU/RAM, utilization_status), billing. Optional query: days=30 (default) or 1–30.",
                "operationId": "getOverview",
                "parameters": [
                    {"name": "provider", "in": "path", "required": True, "schema": {"type": "string", "enum": ["gcp", "aws", "azure", "k8s"]}},
                    {"name": "days", "in": "query", "required": False, "schema": {"type": "integer", "minimum": 1, "maximum": 30, "default": 30}},
                ],
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {"description": "Overview with compute, metrics, billing, summary"},
                    "401": {"description": "Missing or invalid Authorization header", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            }
        },
        "/api/v1/demo/projects": {
            "get": {
                "tags": ["Demo"],
                "summary": "List demo projects",
                "description": "Returns two mock projects (acme-prod and acme-staging) for the try-it-out flow. No authentication required.",
                "operationId": "demoProjects",
                "responses": {
                    "200": {
                        "description": "List of mock projects",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Project"}},
                                "example": [
                                    {"id": "demo-project-prod", "name": "acme-prod", "provider": "gcp"},
                                    {"id": "demo-project-staging", "name": "acme-staging", "provider": "gcp"},
                                ],
                            }
                        },
                    },
                },
            }
        },
        "/api/v1/demo/overview": {
            "get": {
                "tags": ["Demo"],
                "summary": "Demo dashboard overview",
                "description": "Returns mock overview data for the try-it-out flow. Supports ?project= to filter by demo project. No authentication required.",
                "operationId": "demoOverview",
                "parameters": [
                    {
                        "name": "project",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "enum": ["demo-project-prod", "demo-project-staging"]},
                        "description": "Filter by demo project. Omit for aggregated all-projects view.",
                    },
                ],
                "responses": {
                    "200": {"description": "Mock overview with summary, highlights, and billing"},
                },
            }
        },
        "/api/v1/{provider}/billing": {
            "get": {
                "tags": ["Providers"],
                "summary": "Get billing data",
                "description": "Return project billing account info (enabled, account id, display name, currency). top_services and anomalies require BigQuery billing export.",
                "operationId": "getBilling",
                "parameters": [
                    {
                        "name": "provider",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "enum": ["gcp", "aws", "azure", "k8s"]},
                    }
                ],
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Billing report",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CostReport"},
                            }
                        },
                    },
                    "401": {"description": "Missing or invalid Authorization header", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            }
        },
    },
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "connectionId",
                "description": "The connectionId returned from POST /api/v1/connect",
            }
        },
        "schemas": {
            "ConnectRequest": {
                "type": "object",
                "required": ["provider", "credentials"],
                "properties": {
                    "provider": {
                        "type": "string",
                        "enum": ["gcp", "aws", "azure", "k8s"],
                        "description": "Cloud provider identifier",
                    },
                    "credentials": {
                        "type": "object",
                        "description": "Provider-specific credential fields",
                    },
                },
            },
            "ConnectResponse": {
                "type": "object",
                "properties": {
                    "connectionId": {
                        "type": "string",
                        "format": "uuid",
                        "description": "Opaque token — store in localStorage, send as Authorization: Bearer <connectionId>",
                    },
                    "provider": {"type": "string"},
                },
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                },
            },
            "Project": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "provider": {"type": "string", "enum": ["gcp", "aws", "azure", "k8s"]},
                },
            },
            "Resource": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "provider": {"type": "string"},
                    "region": {"type": "string"},
                    "resource_type": {"type": "string", "enum": ["vm", "disk", "ip"]},
                    "status": {"type": "string", "enum": ["healthy", "warning", "waste"]},
                    "waste_reason": {"type": "string", "enum": ["idle", "stopped", "unattached", "oversized", "unused", "none"]},
                    "monthly_cost_usd": {"type": "number"},
                    "recommended_action": {"type": "string"},
                },
            },
            "Metric": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "format": "date-time"},
                    "cpu_percent": {"type": "number", "nullable": True},
                    "ram_percent": {"type": "number", "nullable": True},
                },
            },
            "CostReport": {
                "type": "object",
                "properties": {
                    "billing_enabled": {"type": "boolean"},
                    "billing_account_id": {"type": "string", "nullable": True},
                    "billing_account_display_name": {"type": "string", "nullable": True},
                    "currency_code": {"type": "string"},
                    "top_services": {"type": "array", "items": {"type": "object"}, "description": "Requires BigQuery billing export"},
                    "month_over_month_delta": {"type": "number", "nullable": True},
                    "anomalies": {"type": "array", "items": {"type": "object"}},
                },
            },
        }
    },
}
