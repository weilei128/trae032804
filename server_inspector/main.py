#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import yaml

from ssh_client import SSHClient
from system_collector import SystemCollector
from docker_collector import DockerCollector
from pdf_reporter import PDFReporter


class ServerInspector:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.results: List[Dict] = []

    def _load_config(self, config_path: str) -> dict:
        if not os.path.exists(config_path):
            return self._get_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _get_default_config(self) -> dict:
        return {
            'servers': [],
            'inspection': {
                'ports_to_check': [22, 80, 443, 3306, 6379, 8080, 27017],
                'processes_to_check': ['nginx', 'mysql', 'redis', 'java', 'python', 'docker']
            },
            'report': {
                'output_dir': './reports',
                'filename_prefix': 'server_inspection'
            }
        }

    def inspect_server(self, server_config: dict) -> Dict:
        host = server_config['host']
        port = server_config.get('port', 22)
        username = server_config.get('username', 'root')
        key_path = server_config.get('key_path')
        password = server_config.get('password')
        
        print(f"Connecting to server: {host}...")
        
        result = {
            'host': host,
            'hostname': 'N/A',
            'os': 'N/A',
            'kernel': 'N/A',
            'uptime': 'N/A',
            'cpu': None,
            'memory': None,
            'disks': [],
            'ports': [],
            'processes': [],
            'docker': None
        }
        
        ssh = SSHClient(host, port, username, key_path, password)
        
        if not ssh.connect():
            print(f"Failed to connect to {host}")
            return result
        
        try:
            print(f"Collecting system information from {host}...")
            
            _, hostname, _ = ssh.execute("hostname")
            result['hostname'] = hostname.strip()
            
            _, os_info, _ = ssh.execute("cat /etc/os-release | grep PRETTY_NAME | cut -d'\"' -f2")
            result['os'] = os_info.strip() or 'Unknown'
            
            _, kernel, _ = ssh.execute("uname -r")
            result['kernel'] = kernel.strip()
            
            _, uptime, _ = ssh.execute("uptime -p 2>/dev/null || uptime")
            result['uptime'] = uptime.strip().replace('up ', '')
            
            system_collector = SystemCollector(ssh)
            
            print(f"  - Collecting CPU info...")
            result['cpu'] = system_collector.get_cpu_info()
            
            print(f"  - Collecting memory info...")
            result['memory'] = system_collector.get_memory_info()
            
            print(f"  - Collecting disk info...")
            result['disks'] = system_collector.get_disk_info()
            
            ports_to_check = self.config.get('inspection', {}).get('ports_to_check', [])
            print(f"  - Checking TCP ports...")
            result['ports'] = system_collector.get_tcp_ports(ports_to_check)
            
            processes_to_check = self.config.get('inspection', {}).get('processes_to_check', [])
            print(f"  - Checking processes...")
            result['processes'] = system_collector.get_processes(processes_to_check)
            
            print(f"  - Collecting Docker info...")
            docker_collector = DockerCollector(ssh)
            result['docker'] = docker_collector.get_docker_info()
            
            print(f"Server {host} inspection completed!")
            
        except Exception as e:
            print(f"Error inspecting {host}: {e}")
        finally:
            ssh.close()
        
        return result

    def run_inspection(self) -> List[Dict]:
        servers = self.config.get('servers', [])
        
        if not servers:
            print("No servers configured. Please edit config.yaml")
            return []
        
        print(f"Starting inspection of {len(servers)} server(s)...\n")
        
        for server in servers:
            result = self.inspect_server(server)
            self.results.append(result)
            print()
        
        return self.results

    def generate_report(self) -> str:
        report_config = self.config.get('report', {})
        output_dir = report_config.get('output_dir', './reports')
        filename_prefix = report_config.get('filename_prefix', 'server_inspection')
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        print(f"\nGenerating PDF report: {output_path}")
        
        reporter = PDFReporter(output_path)
        reporter.generate_report(self.results)
        
        print(f"Report generated successfully: {output_path}")
        return output_path


def main():
    config_path = "config.yaml"
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    inspector = ServerInspector(config_path)
    
    inspector.run_inspection()
    
    if inspector.results:
        inspector.generate_report()


if __name__ == "__main__":
    main()
