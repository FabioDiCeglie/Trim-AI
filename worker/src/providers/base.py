from abc import ABC, abstractmethod


class CloudProvider(ABC):
    """
    Abstract base class all cloud provider adapters must implement.

    Every provider (GCP, AWS, Azure, K8s) implements these five methods
    and returns normalized dicts. The router never needs to know which
    provider it's talking to — it just calls these methods.
    """

    @abstractmethod
    async def get_projects(self) -> list[dict]:
        """List projects / accounts / subscriptions accessible with these credentials."""
        ...

    @abstractmethod
    async def get_compute(self) -> list[dict]:
        """Return VMs, disks, and IPs — flagging idle, stopped, unattached, or oversized ones."""
        ...

    @abstractmethod
    async def get_metrics(self, request) -> list[dict]:
        """Return CPU / RAM time-series for compute resources."""
        ...

    @abstractmethod
    async def get_billing(self) -> dict:
        """Return cost breakdown and spend anomalies."""
        ...

    @abstractmethod
    async def get_overview(self, request) -> dict:
        """Return single dashboard payload: compute, metrics (with utilization), billing, summary."""
        ...
