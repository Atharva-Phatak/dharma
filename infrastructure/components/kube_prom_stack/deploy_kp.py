import pulumi
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts
import pulumi_kubernetes as k8s
from infrastructure.helper.secrets import generate_grafana_credentials


def deploy_kp_stack(
    depends_on: list,
    provider: k8s.Provider,
    namespace: str,
    project_id: str,
) -> Chart:
    grafana_username, grafana_password = generate_grafana_credentials(
        project_id=project_id, environment_slug="dev"
    )

    prometheus_chart = Chart(
        "prometheus-stack",
        ChartOpts(
            chart="kube-prometheus-stack",
            version="81.4.0",
            fetch_opts=FetchOpts(
                repo="https://prometheus-community.github.io/helm-charts",
            ),
            namespace=namespace,
            values={
                # --- LEAN REPLICA SETTINGS ---
                "prometheusOperator": {"replicaCount": 1},
                "kube-state-metrics": {"replicaCount": 1},
                "grafana": {
                    "enabled": True,
                    "replicas": 1,
                    "adminUser": "admin",
                    "adminPassword": grafana_password,
                    "ingress": {
                        "enabled": True,
                        "ingressClassName": "nginx",
                        "annotations": {
                            "nginx.ingress.kubernetes.io/rewrite-target": "/",
                            "nginx.ingress.kubernetes.io/ssl-redirect": "false",
                            "nginx.ingress.kubernetes.io/proxy-body-size": "64m",
                            "nginx.ingress.kubernetes.io/proxy-connect-timeout": "300",
                            "nginx.ingress.kubernetes.io/proxy-send-timeout": "300",
                            "nginx.ingress.kubernetes.io/proxy-read-timeout": "300",
                        },
                        "labels": {},
                        "hosts": ["grafana-palebluedot.io"],
                        "path": "/",
                        "pathType": "Prefix",
                    },
                },
                "alertmanager": {"alertmanagerSpec": {"replicas": 1}},
                "prometheus": {
                    "prometheusSpec": {
                        "replicas": 1,
                        "serviceMonitorSelectorNilUsesHelmValues": False,
                        "retention": "1d",
                        "resources": {
                            "requests": {"cpu": "100m", "memory": "400Mi"},
                            "limits": {"cpu": "500m", "memory": "1Gi"},
                        },
                        "storageSpec": {
                            "volumeClaimTemplate": {
                                "spec": {
                                    "storageClassName": "standard",
                                    "accessModes": ["ReadWriteOnce"],
                                    "resources": {"requests": {"storage": "10Gi"}},
                                }
                            }
                        },
                    },
                    "additionalServiceMonitors": [
                        {
                            "name": "vllm-engine-monitor",
                            "selector": {
                                "matchLabels": {
                                    "environment": "dev",
                                    "service": "ocr_engine",  # ← Changed from "ocr" to "ocr_engine"
                                }
                            },
                            "namespaceSelector": {"matchNames": ["zenml"]},
                            "endpoints": [{"port": "service-port", "path": "/metrics"}],
                        },
                        {
                            "name": "vllm-router-monitor",
                            "selector": {
                                "matchLabels": {
                                    "environment": "dev",
                                    "release": "router",
                                }
                            },
                            "namespaceSelector": {"matchNames": ["zenml"]},
                            "endpoints": [{"port": "router-sport", "path": "/metrics"}],
                        },
                    ],
                },
                # --- PROMETHEUS ADAPTER FOR CUSTOM METRICS (HPA) ---
                "prometheus-adapter": {
                    "enabled": True,
                    "prometheus": {
                        "url": f"http://prometheus-stack-kube-prom-prometheus.{namespace}.svc",
                        "port": 9090,
                    },
                    "logLevel": 1,
                    "rules": {
                        "default": True,
                        "custom": [
                            # vLLM num_requests_waiting metric for HPA
                            {
                                "seriesQuery": '{__name__=~"^vllm:num_requests_waiting$"}',
                                "resources": {
                                    "overrides": {
                                        "namespace": {"resource": "namespace"}
                                    }
                                },
                                "name": {
                                    "matches": "",
                                    "as": "vllm_num_requests_waiting",
                                },
                                "metricsQuery": "sum by(namespace) (vllm:num_requests_waiting)",
                            },
                            # vLLM num_incoming_requests_total by model name
                            {
                                "seriesQuery": '{__name__=~"^vllm:num_incoming_requests_total$"}',
                                "resources": {
                                    "overrides": {
                                        "namespace": {"resource": "namespace"}
                                    }
                                },
                                "name": {
                                    "matches": "",
                                    "as": "vllm_num_incoming_requests_total",
                                },
                                "metricsQuery": "sum by(namespace, model) (vllm:num_incoming_requests_total)",
                            },
                        ],
                    },
                },
                # --- K8S METRICS & CLEANUP ---
                "nodeExporter": {"enabled": True},
                "kubeStateMetrics": {"enabled": True},
                "kubeScheduler": {"enabled": False},
                "kubeEtcd": {"enabled": False},
                "kubeControllerManager": {"enabled": False},
                "additionalPrometheusRulesMap": {
                    "vllm-rules": {
                        "groups": [
                            {
                                "name": "vllm-alerts",
                                "rules": [
                                    {
                                        "alert": "vLLMHighQueueSize",
                                        "expr": "vllm:num_requests_waiting > 10",
                                        "for": "2m",
                                        "labels": {"severity": "warning"},
                                        "annotations": {
                                            "summary": "vLLM queue is backing up",
                                            "description": "Namespace {{ $labels.namespace }} has {{ $value }} requests waiting.",
                                        },
                                    }
                                ],
                            }
                        ]
                    }
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
            custom_timeouts=pulumi.CustomTimeouts(create="10m"),
            depends_on=depends_on,
        ),
    )

    pulumi.export("prometheus_status", prometheus_chart.ready)
    pulumi.export("grafana_url", "http://grafana-palebluedot.io")
    return prometheus_chart
