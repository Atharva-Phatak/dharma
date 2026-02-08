import pulumi
import pulumi_kubernetes as k8s


def deploy_nvidia_runtime_class(provider: k8s.Provider, depends_on: list):
    # Create NVIDIA RuntimeClass
    nvidia_runtime_class = k8s.node.v1.RuntimeClass(
        "nvidia-runtime-class",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="nvidia",
        ),
        handler="nvidia",
        opts=pulumi.ResourceOptions(
            provider=provider,
            custom_timeouts=pulumi.CustomTimeouts(create="10m"),
            depends_on=depends_on,
        ),
    )
    # Export the RuntimeClass name
    pulumi.export("runtime_class_name", nvidia_runtime_class.metadata["name"])
