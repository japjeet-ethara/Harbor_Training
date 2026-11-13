from pathlib import Path

from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.task.config import NetworkMode


class OfflineDocker(DockerEnvironment):
    @classmethod
    def _requires_egress_control(cls, *, startup_network_policy, phase_network_policies):
        if any(policy.network_mode != NetworkMode.NO_NETWORK for policy in [startup_network_policy, *phase_network_policies]):
            raise ValueError('This profile supports only no-network policies')
        return False

    @property
    def capabilities(self):
        return super().capabilities.model_copy(update={'disable_internet': True, 'mounted': False})

    @property
    def _docker_compose_paths(self):
        return [*super()._docker_compose_paths, Path(__file__).with_name('offline-compose.yaml')]

    async def _apply_network_policy(self, policy):
        if policy.network_mode != NetworkMode.NO_NETWORK:
            raise ValueError('This profile supports only no-network policies')
