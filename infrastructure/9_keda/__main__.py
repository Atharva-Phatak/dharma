from infrastructure.components.keda.deploy_keda import deploy_keda
from infrastructure.helper.namespace import create_namespace
from infrastructure.helper.provider import get_k8s_provider
from infrastructure.helper.config import load_config

provider = get_k8s_provider()
cfg = load_config()

keda_namespace = create_namespace(
    provider=provider,
    namespace = "keda"
)
_ = deploy_keda(
    provider=provider,
    namespace=keda_namespace.metadata["name"],
)