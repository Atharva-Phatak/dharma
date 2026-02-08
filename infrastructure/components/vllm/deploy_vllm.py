import pulumi
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts
import pulumi_kubernetes as k8s
import os


def deploy_vllm(provider: k8s.Provider, namespace: str):
    hf_token = os.getenv("HF_TOKEN")

    service_account = k8s.core.v1.ServiceAccount(
        "vllm-router-service-account",
        metadata={
            "name": "vllm-stack-router-service-account",
            "namespace": namespace,
        },
        opts=pulumi.ResourceOptions(provider=provider),
    )

    vllm_chart = Chart(
        "vllm-stack",
        ChartOpts(
            chart="vllm-stack",
            version="0.1.9",  # Check latest
            fetch_opts=FetchOpts(
                repo="https://vllm-project.github.io/production-stack",
            ),
            namespace=namespace,
            values={
                "servingEngineSpec": {
                    "labels": {
                        "environment": "dev",
                        "service": "ocr_engine",
                        "release": "engine",
                    },
                    "modelSpec": [
                        {
                            "name": "nanonets-ocr2-3b",
                            "serviceAccountName": "vllm-stack-router-service-account",
                            "annotations": {
                                "model": "nanonets-ocr2-3b",
                            },
                            "repository": "vllm/vllm-openai",
                            "tag": "v0.10.0",
                            "modelURL": "/models/Nanonets-OCR2-3B",
                            "replicaCount": 1,
                            "requestCPU": 10,
                            "requestMemory": "8Gi",
                            "requestGPU": 1,
                            "imagePullPolicy": "IfNotPresent",
                            "vllmConfig": {
                                "v0": "1",
                                "dtype": "bfloat16",
                                "maxNumSeqs": 10,
                                # OCR doesn't need huge context
                                "gpu_memory_utilization": 0.85,
                                "extraArgs": [
                                    "--mm-processor-kwargs",
                                    '{"min_pixels": 784, "max_pixels": 4096000}',
                                    "--limit_mm_per_prompt",
                                    '{"image": 5, "video": 0}',
                                    "--max-model-len",
                                    "16000",
                                ],
                            },
                            "keda": {
                                "enabled": True,
                                "minReplicaCount": 0,  # Allow scaling to zero
                                "maxReplicaCount": 1,
                                "idleReplicaCount": 0,
                                "triggers": [
                                    # Queue-based scaling
                                    {
                                        "type": "prometheus",
                                        "metadata": {
                                            "serverAddress": "http://prometheus-stack-kube-prom-prometheus.monitoring.svc:9090",
                                            "metricName": "vllm:num_requests_waiting",
                                            "query": "vllm:num_requests_waiting",
                                            "threshold": "5",
                                        },
                                    },
                                    # Traffic-based keepalive (prevents scale-to-zero when traffic exists)
                                    {
                                        "type": "prometheus",
                                        "metadata": {
                                            "serverAddress": "http://prometheus-stack-kube-prom-prometheus.monitoring.svc:9090",
                                            "metricName": "vllm:incoming_keepalive",
                                            "query": "sum(rate(vllm:num_incoming_requests_total[1m]) > bool 0)",
                                            "threshold": "1",
                                        },
                                    },
                                ],
                            },
                            # 🔌 Attach existing PVC
                            "extraVolumes": [
                                {
                                    "name": "model-vol",
                                    "persistentVolumeClaim": {"claimName": "model-pvc"},
                                }
                            ],
                            # 📂 Mount it inside container
                            "extraVolumeMounts": [
                                {
                                    "name": "model-vol",
                                    "mountPath": "/models",
                                    "readOnly": True,
                                }
                            ],
                            "env": [
                                {"name": "HUGGING_FACE_HUB_TOKEN", "value": hf_token},
                                {"name": "HUGGING_FACE_HUB_CACHE", "value": "/models"},
                                {"name": "TRANSFORMERS_CACHE", "value": "/models"},
                                {"name": "HF_HUB_OFFLINE", "value": "1"},
                                {"name": "TRANSFORMERS_OFFLINE", "value": "1"},
                            ],
                        }
                    ],
                },
                "routerSpec": {
                    "labels": {
                        "environment": "dev",
                    },
                    "imagePullPolicy": "IfNotPresent",
                    "resources": {
                        "requests": {"cpu": "400m", "memory": "1500Mi"},
                        "limits": {"memory": "2000Mi"},
                    },
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
            custom_timeouts=pulumi.CustomTimeouts(create="10m"),
            replace_on_changes=["spec"],
            depends_on=[service_account],
        ),
    )
    pulumi.export("vllm_helm_chart", vllm_chart.ready)
    return vllm_chart
