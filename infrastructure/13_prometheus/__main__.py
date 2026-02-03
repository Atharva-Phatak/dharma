from infrastructure.helper.namespace import create_namespace
from infrastructure.helper.provider import get_k8s_provider
import pulumi
from infrastructure.components.prometheus.deploy_prometheus import deploy_prometheus
from infrastructure.helper.config import load_config

provider = get_k8s_provider()
cfg = load_config()
monitoring_namespace = create_namespace(
    provider=provider,
    namespace="monitoring",
)
# Deploy prometheus and grafana
prometheus_chart = deploy_prometheus(
    depends_on=[monitoring_namespace],
    provider=provider,
    namespace="monitoring",
    project_id=cfg.infiscal_project_id,
)
pulumi.export("monitoring_namespace", monitoring_namespace.metadata["name"])
