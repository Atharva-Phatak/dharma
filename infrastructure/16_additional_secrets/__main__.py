import infrastructure.helper.secrets as secrets
from infrastructure.helper.provider import get_k8s_provider
from infrastructure.helper.config import load_config
import pulumi
from infrastructure.helper.namespace import create_namespace

cfg = load_config()
provider = get_k8s_provider()
pconfig = pulumi.Config()


external_secret_namespace = create_namespace(
    provider=provider, namespace="external-secrets"
)

_ = secrets.create_k8s_infiscal_secret_token(
    k8s_provider=provider,
    namespace="external-secrets",
    depends_on=[external_secret_namespace],
)

_ = secrets.generate_slack_secret(
    project_id=cfg.infiscal_project_id,
    environment_slug="dev",
)
_ = secrets.generate_gh_secret(
    project_id=cfg.infiscal_project_id,
    environment_slug="dev",
)
_ = secrets.generate_gh_secret(
    project_id=cfg.infiscal_project_id,
    environment_slug="dev",
)
_ = secrets.generate_grafana_credentials(
    project_id=cfg.infiscal_project_id,
    environment_slug="dev",
)
_ = secrets.generate_minio_secret(
    project_id=cfg.infiscal_project_id,
    environment_slug="dev",
)
_ = secrets.generate_minio_secret(
    project_id=cfg.infiscal_project_id,
    environment_slug="dev",
)
_ = secrets.generate_zenml_jwt_secret(
    project_id=cfg.infiscal_project_id,
    environment_slug="dev",
)
