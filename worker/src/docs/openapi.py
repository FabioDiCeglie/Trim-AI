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
    },
    "components": {
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
        }
    },
}
