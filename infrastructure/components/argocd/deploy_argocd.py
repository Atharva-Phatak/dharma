import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts


def deploy_argocd(provider: k8s.Provider, depends_on: list, namespace: str):
    argocd_chart = Chart(
        "argocd",
        ChartOpts(
            chart="argo-cd",
            version="9.4.1",
            fetch_opts=FetchOpts(
                repo="https://argoproj.github.io/argo-helm",
            ),
            namespace=namespace,
            values={
                "global": {"domain": "argocd.deploy.com"},
                "configs": {
                    "params": {
                        "server.insecure": "true"  # Must be string "true", not boolean
                    }
                },
                "server": {
                    "service": {"servicePortHttp": 80, "servicePortHttps": 443},
                    "ingress": {
                        "enabled": True,
                        "ingressClassName": "nginx",
                        "annotations": {
                            "nginx.ingress.kubernetes.io/ssl-redirect": "false",
                            "nginx.ingress.kubernetes.io/force-ssl-redirect": "false",
                            "nginx.ingress.kubernetes.io/backend-protocol": "HTTP",
                            "nginx.ingress.kubernetes.io/proxy-body-size": "64m",
                            "nginx.ingress.kubernetes.io/proxy-connect-timeout": "300",
                            "nginx.ingress.kubernetes.io/proxy-send-timeout": "300",
                            "nginx.ingress.kubernetes.io/proxy-read-timeout": "300",
                        },
                        "hosts": ["argocd.deploy.com"],
                        "tls": [],
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "argocd-server",
                                        "port": {"number": 80},
                                    }
                                },
                            }
                        ],
                    },
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
            custom_timeouts=pulumi.CustomTimeouts(create="10m"),
            depends_on=depends_on,
        ),
    )

    pulumi.export("argocd_chart", argocd_chart.ready)
    return argocd_chart
