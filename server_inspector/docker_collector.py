from dataclasses import dataclass
from typing import List, Optional
from ssh_client import SSHClient


@dataclass
class DockerContainer:
    container_id: str
    name: str
    image: str
    status: str
    state: str
    ports: str


@dataclass
class DockerImage:
    repository: str
    tag: str
    image_id: str
    size: str


@dataclass
class DockerInfo:
    installed: bool
    version: str
    running_containers: int
    total_containers: int
    total_images: int
    containers: List[DockerContainer]
    images: List[DockerImage]


class DockerCollector:
    def __init__(self, ssh_client: SSHClient):
        self.ssh = ssh_client

    def is_docker_installed(self) -> bool:
        _, output, _ = self.ssh.execute("which docker")
        return bool(output.strip())

    def get_docker_version(self) -> str:
        _, output, _ = self.ssh.execute("docker --version 2>/dev/null")
        return output.strip() or "Unknown"

    def get_containers(self) -> List[DockerContainer]:
        _, output, _ = self.ssh.execute(
            'docker ps -a --format "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.State}}|{{.Ports}}" 2>/dev/null'
        )
        containers = []
        
        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 5:
                containers.append(DockerContainer(
                    container_id=parts[0],
                    name=parts[1],
                    image=parts[2],
                    status=parts[3],
                    state=parts[4],
                    ports=parts[5] if len(parts) > 5 else ""
                ))
        
        return containers

    def get_images(self) -> List[DockerImage]:
        _, output, _ = self.ssh.execute(
            'docker images --format "{{.Repository}}|{{.Tag}}|{{.ID}}|{{.Size}}" 2>/dev/null'
        )
        images = []
        
        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 4:
                images.append(DockerImage(
                    repository=parts[0],
                    tag=parts[1],
                    image_id=parts[2],
                    size=parts[3]
                ))
        
        return images

    def get_docker_info(self) -> DockerInfo:
        installed = self.is_docker_installed()
        
        if not installed:
            return DockerInfo(
                installed=False,
                version="Not Installed",
                running_containers=0,
                total_containers=0,
                total_images=0,
                containers=[],
                images=[]
            )
        
        version = self.get_docker_version()
        containers = self.get_containers()
        images = self.get_images()
        
        running_containers = sum(1 for c in containers if c.state == "running")
        
        return DockerInfo(
            installed=True,
            version=version,
            running_containers=running_containers,
            total_containers=len(containers),
            total_images=len(images),
            containers=containers,
            images=images
        )

    def get_container_stats(self) -> List[dict]:
        _, output, _ = self.ssh.execute(
            'docker stats --no-stream --format "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}" 2>/dev/null'
        )
        stats = []
        
        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 4:
                stats.append({
                    'name': parts[0],
                    'cpu_percent': parts[1],
                    'memory_usage': parts[2],
                    'network_io': parts[3]
                })
        
        return stats
