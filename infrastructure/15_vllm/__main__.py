from infrastructure.components.vllm.deploy_vllm import deploy_vllm
from infrastructure.helper.provider import get_k8s_provider
from infrastructure.helper.config import load_config
import pulumi

cfg = load_config()
provider = get_k8s_provider()
pconfig = pulumi.Config()
namespace_name = pconfig.require("namespace")
_ = deploy_vllm(
    provider=provider,
    namespace=namespace_name,
)
