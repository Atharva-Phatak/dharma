import typer
from rich.console import Console
from infrastructure.deploy import (
    deploy_sequentially,
    refresh_sequentially,
    destroy_singular_stack,
)
import os
from dotenv import load_dotenv

app = typer.Typer()
console = Console()


# Load secrets
secret_path: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".secrets")
)
console.print(f"🔐 Loading secrets from: {secret_path}")
load_dotenv(os.path.join(secret_path, ".env"))


class InfraDeployer:
    def __init__(self, operation: str, group: str = "default"):
        self.operation = operation
        self.group = group
        self.passphrase = None
        if not self.passphrase:
            self.passphrase = "password"
            os.environ["PULUMI_CONFIG_PASSPHRASE"] = self.passphrase

    def deploy(self):
        console.print(f"✅ [green]Deploying group:[/green] {self.group}")

        if self.operation == "create" and self.group == "default":
            deploy_sequentially()
        else:
            raise ValueError(
                f"Unsupported operation '{self.operation}' for group '{self.group}'."
            )

    def refresh(self):
        console.print(f"Refreshing {self.group}")

        if self.operation == "refresh" and self.group == "default":
            refresh_sequentially()
        else:
            raise ValueError(
                f"Unsupported operation '{self.operation}' for group '{self.group}'."
            )

    def destroy(self, stack_name: str):
        console.print(f"Deleting {stack_name}")
        if self.operation == "destroy":
            destroy_singular_stack(stack_name)
        else:
            raise ValueError(
                f"Unsupported operation '{self.operation}' for group '{self.group}'."
            )
