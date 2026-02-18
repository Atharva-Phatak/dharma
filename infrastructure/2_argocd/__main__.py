from infrastructure.components.argocd.deploy_argocd import deploy_argocd
from infrastructure.helper.namespace import create_namespace
from infrastructure.helper.provider import get_k8s_provider


provider = get_k8s_provider()

argo_ns = create_namespace(provider=provider, namespace="argocd")

_ = deploy_argocd(
    provider=provider,
    namespace=argo_ns.metadata["name"],
    depends_on=[argo_ns],
)
