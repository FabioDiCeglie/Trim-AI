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
                "description": "Return CPU / RAM time-series for compute resources.",
                "operationId": "getMetrics",
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
        "/api/v1/{provider}/billing": {
            "get": {
                "tags": ["Providers"],
                "summary": "Get billing data",
                "description": "Return cost breakdown and spend anomalies.",
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
                    "provider": {"type": "string"},
                    "project_id": {"type": "string"},
                    "month": {"type": "string", "pattern": "^\\d{4}-\\d{2}$"},
                    "total_cost_usd": {"type": "number"},
                    "previous_month_cost_usd": {"type": "number", "nullable": True},
                    "services": {"type": "array", "items": {"type": "object"}},
                    "anomalies": {"type": "array", "items": {"type": "object"}},
                },
            },
        }
    },
}
