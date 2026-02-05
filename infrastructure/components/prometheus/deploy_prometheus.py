import pulumi
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts
import pulumi_kubernetes as k8s
from infrastructure.helper.secrets import generate_grafana_credentials


def deploy_prometheus(
    depends_on: list,
    provider: k8s.Provider,
    namespace: str,
    project_id: str,
) -> Chart:
    grafana_username, grafana_password = generate_grafana_credentials(
        project_id=project_id, environment_slug="dev"
    )

    prometheus_chart = Chart(
        "prometheus",
        ChartOpts(
            chart="prometheus",
            version="27.20.1",  # Check latest
            fetch_opts=FetchOpts(
                repo="https://prometheus-community.github.io/helm-charts",
            ),
            namespace=namespace,
            values={
                "server": {
                    "resources": {
                        "requests": {
                            "cpu": "250m",
                            "memory": "512Mi",
                        },
                        "limits": {
                            "cpu": "500m",
                            "memory": "1Gi",
                        },
                    },
                    "service": {"type": "ClusterIP"},
                    "persistentVolume": {
                        "enabled": True,
                        "storageClass": "standard",
                    },
                },
                "alertmanager": {"enabled": True},
                "pushgateway": {"enabled": False},
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
            custom_timeouts=pulumi.CustomTimeouts(create="10m"),
            depends_on=depends_on,
        ),
    )
    pulumi.export("prometheus_status", prometheus_chart.ready)
    return prometheus_chart
