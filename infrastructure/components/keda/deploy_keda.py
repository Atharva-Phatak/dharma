import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts


def deploy_keda(
    provider: k8s.Provider, namespace: str, depends_on: list = None
) -> Chart:
    """
    Deploy KEDA (Kubernetes Event-Driven Autoscaling) with default settings
    """

    keda_chart = Chart(
        "keda",
        ChartOpts(
            chart="keda",
            version="2.18.2",
            fetch_opts=FetchOpts(
                repo="https://kedacore.github.io/charts",
            ),
            namespace=namespace,
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
            custom_timeouts=pulumi.CustomTimeouts(create="10m"),
            depends_on=depends_on or [],
        ),
    )
    pulumi.export("keda_status", keda_chart.ready)
    return keda_chart
