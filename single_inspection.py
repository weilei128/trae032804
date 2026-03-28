#!/usr/bin/env python3
"""
Linux服务器单次自动化巡检脚本
执行一次巡检并生成PDF报表
"""
import sys
from datetime import datetime
from typing import Dict, Any, List
import config
from ssh_client import SSHClient
from system_collector import SystemCollector
from service_collector import ServiceCollector
from docker_collector import DockerCollector
from pdf_reporter import PDFReporter


def inspect_server(server_config: Dict[str, Any]) -> Dict[str, Any]:
    """巡检单台服务器"""
    result = {
        'inspection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'server_name': server_config.get('name', server_config['host']),
        'host': server_config['host'],
        'system': {},
        'cpu': {},
        'memory': {},
        'disk': [],
        'ports': [],
        'listening_ports': [],
        'processes': [],
        'docker_summary': {},
        'containers': [],
        'images': []
    }
    
    ssh = SSHClient(
        host=server_config['host'],
        port=server_config['port'],
        username=server_config['username'],
        key_file=server_config.get('key_file'),
        password=server_config.get('password')
    )
    
    try:
        if not ssh.connect():
            result['error'] = 'SSH连接失败'
            return result
        
        print(f"  [{server_config['host']}] SSH连接成功")
        
        sys_collector = SystemCollector(ssh)
        result['system'] = sys_collector.get_system_info()
        result['system']['host'] = server_config['host']
        result['cpu'] = sys_collector.get_cpu_info()
        result['memory'] = sys_collector.get_memory_info()
        result['disk'] = sys_collector.get_disk_info()
        print(f"  [{server_config['host']}] 系统信息采集完成")
        
        svc_collector = ServiceCollector(ssh)
        result['ports'] = svc_collector.check_tcp_ports()
        result['listening_ports'] = svc_collector.get_all_listening_ports()
        result['processes'] = svc_collector.check_processes()
        print(f"  [{server_config['host']}] 服务状态采集完成")
        
        docker_collector = DockerCollector(ssh)
        result['docker_summary'] = docker_collector.get_docker_summary()
        result['containers'] = docker_collector.get_containers()
        result['images'] = docker_collector.get_images()
        print(f"  [{server_config['host']}] Docker信息采集完成")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"  [{server_config['host']}] 采集异常: {e}")
    finally:
        ssh.disconnect()
    
    return result


def print_summary(all_data: Dict[str, Any]):
    """打印巡检摘要"""
    print(f"\n{'='*80}")
    print("巡检结果摘要")
    print(f"{'='*80}")
    
    for server_name, data in all_data.items():
        print(f"\n【{server_name}】")
        
        if 'error' in data:
            print(f"  错误: {data['error']}")
            continue
        
        cpu = data.get('cpu', {})
        print(f"  CPU: 使用率 {cpu.get('cpu_usage', 0):.1f}%, "
              f"负载 {cpu.get('load_1min', 0):.2f}/{cpu.get('load_5min', 0):.2f}/{cpu.get('load_15min', 0):.2f}")
        
        mem = data.get('memory', {})
        print(f"  内存: {mem.get('used_mb', 0)}/{mem.get('total_mb', 0)} MB ({mem.get('usage_percent', 0):.1f}%)")
        
        disk = data.get('disk', [])
        for d in disk:
            print(f"  磁盘 [{d.get('mount_point', '')}]: {d.get('used', '')}/{d.get('size', '')} ({d.get('usage_percent', 0)}%)")
        
        docker = data.get('docker_summary', {})
        if docker.get('installed'):
            print(f"  Docker: {docker.get('version', '')}, "
                  f"容器 {docker.get('containers_running', 0)}/{docker.get('containers_total', 0)} 运行中")
        else:
            print(f"  Docker: 未安装")
        
        print(f"  监听端口数: {len(data.get('listening_ports', []))}")
        print(f"  监控进程数: {len(data.get('processes', []))}")


def main():
    """主函数"""
    print(f"\n{'#'*80}")
    print("Linux服务器自动化巡检 - 单次巡检")
    print(f"{'#'*80}")
    
    if len(config.SERVERS) == 0:
        print("错误: 没有配置任何服务器")
        sys.exit(1)
    
    print(f"\n开始巡检，共 {len(config.SERVERS)} 台服务器...")
    
    all_data = {}
    
    for server_config in config.SERVERS:
        server_name = server_config.get('name', server_config['host'])
        print(f"\n正在巡检服务器: {server_name} ({server_config['host']})")
        
        server_data = inspect_server(server_config)
        all_data[server_name] = server_data
    
    print_summary(all_data)
    
    print(f"\n{'='*80}")
    print("正在生成PDF报告...")
    
    reporter = PDFReporter()
    report_path = reporter.generate_report(all_data)
    
    print(f"报告已生成: {report_path}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
