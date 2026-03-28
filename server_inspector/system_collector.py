from dataclasses import dataclass
from typing import List, Dict
from ssh_client import SSHClient


@dataclass
class CPUInfo:
    load_1min: float
    load_5min: float
    load_15min: float
    cpu_cores: int
    usage_percent: float


@dataclass
class MemoryInfo:
    total_mb: float
    used_mb: float
    free_mb: float
    usage_percent: float


@dataclass
class DiskInfo:
    filesystem: str
    total_gb: float
    used_gb: float
    available_gb: float
    usage_percent: float
    mount_point: str


@dataclass
class PortInfo:
    port: int
    protocol: str
    state: str
    service: str


@dataclass
class ProcessInfo:
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float


class SystemCollector:
    def __init__(self, ssh_client: SSHClient):
        self.ssh = ssh_client

    def get_cpu_info(self) -> CPUInfo:
        _, output, _ = self.ssh.execute("cat /proc/loadavg && nproc")
        lines = output.strip().split('\n')
        
        load_parts = lines[0].split()
        load_1min = float(load_parts[0])
        load_5min = float(load_parts[1])
        load_15min = float(load_parts[2])
        
        cpu_cores = int(lines[1]) if len(lines) > 1 else 1
        
        _, cpu_output, _ = self.ssh.execute(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
        )
        try:
            usage_percent = float(cpu_output.strip())
        except:
            usage_percent = load_1min / cpu_cores * 100 if cpu_cores > 0 else 0
        
        return CPUInfo(
            load_1min=load_1min,
            load_5min=load_5min,
            load_15min=load_15min,
            cpu_cores=cpu_cores,
            usage_percent=round(usage_percent, 2)
        )

    def get_memory_info(self) -> MemoryInfo:
        _, output, _ = self.ssh.execute("free -m | grep Mem")
        parts = output.split()
        
        total_mb = float(parts[1])
        used_mb = float(parts[2])
        free_mb = float(parts[3])
        usage_percent = (used_mb / total_mb * 100) if total_mb > 0 else 0
        
        return MemoryInfo(
            total_mb=round(total_mb, 2),
            used_mb=round(used_mb, 2),
            free_mb=round(free_mb, 2),
            usage_percent=round(usage_percent, 2)
        )

    def get_disk_info(self) -> List[DiskInfo]:
        _, output, _ = self.ssh.execute("df -h | grep -v tmpfs | grep -v devtmpfs | tail -n +2")
        disks = []
        
        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 6:
                total_str = parts[1].replace('G', '').replace('T', '')
                used_str = parts[2].replace('G', '').replace('T', '')
                avail_str = parts[3].replace('G', '').replace('T', '')
                usage_str = parts[4].replace('%', '')
                
                try:
                    total_gb = float(total_str)
                    if 'T' in parts[1]:
                        total_gb *= 1024
                    used_gb = float(used_str)
                    if 'T' in parts[2]:
                        used_gb *= 1024
                    avail_gb = float(avail_str)
                    if 'T' in parts[3]:
                        avail_gb *= 1024
                    usage_percent = float(usage_str)
                except:
                    continue
                
                disks.append(DiskInfo(
                    filesystem=parts[0],
                    total_gb=round(total_gb, 2),
                    used_gb=round(used_gb, 2),
                    available_gb=round(avail_gb, 2),
                    usage_percent=usage_percent,
                    mount_point=parts[5]
                ))
        
        return disks

    def get_tcp_ports(self, ports_to_check: List[int] = None) -> List[PortInfo]:
        if ports_to_check is None:
            ports_to_check = [22, 80, 443, 3306, 6379, 8080, 27017]
        
        ports = []
        _, output, _ = self.ssh.execute("ss -tlnp")
        
        listening_ports = set()
        for line in output.strip().split('\n')[1:]:
            if 'LISTEN' in line:
                parts = line.split()
                if len(parts) >= 4:
                    local_addr = parts[3]
                    if ':' in local_addr:
                        try:
                            port = int(local_addr.split(':')[-1])
                            listening_ports.add(port)
                        except:
                            pass
        
        for port in ports_to_check:
            state = "LISTENING" if port in listening_ports else "NOT LISTENING"
            ports.append(PortInfo(
                port=port,
                protocol="TCP",
                state=state,
                service=self._get_service_name(port)
            ))
        
        return ports

    def _get_service_name(self, port: int) -> str:
        services = {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            3306: "MySQL",
            6379: "Redis",
            8080: "HTTP-Alt",
            27017: "MongoDB"
        }
        return services.get(port, "Unknown")

    def get_processes(self, process_names: List[str] = None) -> List[ProcessInfo]:
        if process_names is None:
            process_names = ["nginx", "mysql", "redis", "java", "python", "docker"]
        
        processes = []
        for name in process_names:
            _, output, _ = self.ssh.execute(f"pgrep -a {name}")
            if output.strip():
                for line in output.strip().split('\n'):
                    parts = line.split(None, 1)
                    if parts:
                        pid = int(parts[0])
                        cmd = parts[1] if len(parts) > 1 else name
                        
                        _, status_out, _ = self.ssh.execute(f"cat /proc/{pid}/status 2>/dev/null | grep State")
                        status = "running"
                        if status_out.strip():
                            status = status_out.split(':')[1].strip().split()[0]
                        
                        processes.append(ProcessInfo(
                            pid=pid,
                            name=name,
                            status=status,
                            cpu_percent=0.0,
                            memory_percent=0.0
                        ))
        
        return processes

    def check_process_alive(self, process_name: str) -> bool:
        _, output, _ = self.ssh.execute(f"pgrep {process_name}")
        return bool(output.strip())
