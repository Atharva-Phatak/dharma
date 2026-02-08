#!/usr/bin/env python3
"""
Usage: python build.py <pipeline_name> [tag]
"""

import subprocess
from datetime import datetime
from pathlib import Path
from time import time
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


class DockerBuilder:
    """Build Docker images for PBD pipelines with timing."""

    def __init__(
        self,
        pipeline_name: str,
        tag: str = "latest",
        username: str = "atharva-phatak",
        no_cache: bool = True,
    ):
        self.pipeline_name = pipeline_name
        self.tag = tag
        self.username = username
        self.no_cache = no_cache

        # Set up paths
        self.root_dir = Path(__file__).parent.parent.resolve()
        self.dockerfile_path = self.root_dir / pipeline_name / "Dockerfile"
        self.image_name = f"ghcr.io/{username}/{pipeline_name}:{tag}"

        # Timing
        self.script_start_time: Optional[float] = None
        self.validation_duration: int = 0
        self.build_duration: int = 0

    @staticmethod
    def format_duration(duration: int) -> str:
        """Format duration in seconds to human readable format."""
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def _print_header(self):
        """Print build configuration header."""
        console.print(f"⏱️  Starting pipeline build at {datetime.now()}")
        console.print("=" * 40)
        console.print(f"Pipeline: {self.pipeline_name}")
        console.print(f"Tag: {self.tag}")
        console.print(f"Image name: {self.image_name}")
        console.print(f"Dockerfile path: {self.dockerfile_path}")
        console.print(f"Root directory: {self.root_dir}")
        console.print("-" * 40)

    def _validate_dockerfile(self) -> bool:
        """Validate that Dockerfile exists."""
        validation_start_time = time()

        if not self.dockerfile_path.exists():
            console.print(
                f"[red]Error: Dockerfile not found at '{self.dockerfile_path}'[/red]"
            )
            console.print("Available pipelines:")
            pipelines_dir = self.root_dir / "pipelines"

            if pipelines_dir.exists():
                pipelines = [
                    p.name
                    for p in pipelines_dir.iterdir()
                    if p.is_dir() and p.name != "__pycache__"
                ]
                for pipeline in pipelines:
                    console.print(f"  - {pipeline}")
            else:
                console.print("No pipelines found")

            self.validation_duration = int(time() - validation_start_time)
            return False

        self.validation_duration = int(time() - validation_start_time)
        return True

    def _build_image(self) -> bool:
        """Build the Docker image."""
        console.print("🔨 Building Docker image...")

        build_cmd = [
            "docker",
            "build",
            "-f",
            f"{self.pipeline_name}/Dockerfile",
            "-t",
            self.image_name,
            ".",
        ]

        if self.no_cache:
            build_cmd.insert(2, "--no-cache")

        console.print(f"Command: {' '.join(build_cmd)}")
        console.print("-" * 40)

        build_start_time = time()
        try:
            subprocess.run(
                build_cmd,
                cwd=self.root_dir,
                check=True,
            )
            self.build_duration = int(time() - build_start_time)
            return True
        except subprocess.CalledProcessError as e:
            self.build_duration = int(time() - build_start_time)
            console.print(
                f"[red]❌ Error: Docker build failed with exit code: {e.returncode}[/red]"
            )
            console.print(
                f"⏱️  Build duration: {self.format_duration(self.build_duration)}"
            )
            return False

    def _print_summary(self, success: bool):
        """Print timing summary."""
        total_duration = int(time() - self.script_start_time)

        console.print("-" * 40)
        if success:
            console.print("✅ [green]Docker build completed successfully![/green]")
        console.print("")
        console.print("📊 TIMING SUMMARY")
        console.print("=" * 40)
        console.print(
            f"⏱️  Validation time: {self.format_duration(self.validation_duration)}"
        )
        console.print(
            f"🔨 Build time:      {self.format_duration(self.build_duration)}"
        )
        console.print(f"📈 Total time:      {self.format_duration(total_duration)}")
        console.print(f"🕐 Completed at:    {datetime.now()}")
        console.print("")

        if success:
            console.print(f"[green]Image built: {self.image_name}[/green]")

    def build(self) -> bool:
        """Execute the build process."""
        self.script_start_time = time()

        # Print header
        self._print_header()

        # Validate Dockerfile exists
        if not self._validate_dockerfile():
            return False

        # Build the image
        if not self._build_image():
            self._print_summary(success=False)
            return False

        # Print summary
        self._print_summary(success=True)
        return True


if __name__ == "__main__":
    app()
