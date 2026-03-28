#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux服务器批量自动化巡检工具 - PDF报表版本
支持生成PDF格式的巡检报告
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List

import config
from ssh_client import SSHClient
from system_collector import SystemCollector
from service_collector import ServiceCollector
from docker_collector import DockerCollector
from pdf_reporter import PDFReporter
from excel_reporter import ExcelReporter


class ServerInspector:
    """服务器巡检器"""
    
    def __init__(self):
        self.pdf_reporter = PDFReporter()
        self.excel_reporter = ExcelReporter()
    
    def inspect_server(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        对单台服务器执行巡检
        
        Args:
            server_config: 服务器配置字典
            
        Returns:
            巡检结果字典
        """
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
            print(f"  正在连接 {server_config['host']}:{server_config['port']} ...")
            if not ssh.connect():
                result['error'] = 'SSH连接失败'
                print(f"  ❌ SSH连接失败")
                return result
            
            print(f"  ✅ SSH连接成功")
            
            # 采集系统信息
            sys_collector = SystemCollector(ssh)
            result['system'] = sys_collector.get_system_info()
            result['cpu'] = sys_collector.get_cpu_info()
            result['memory'] = sys_collector.get_memory_info()
            result['disk'] = sys_collector.get_disk_info()
            print(f"  ✅ 系统信息采集完成")
            
            # 采集服务信息
            svc_collector = ServiceCollector(ssh)
            result['ports'] = svc_collector.check_tcp_ports()
            result['listening_ports'] = svc_collector.get_all_listening_ports()
            result['processes'] = svc_collector.check_processes()
            print(f"  ✅ 服务状态采集完成")
            
            # 采集Docker信息
            docker_collector = DockerCollector(ssh)
            result['docker_summary'] = docker_collector.get_docker_summary()
            result['containers'] = docker_collector.get_containers()
            result['images'] = docker_collector.get_images()
            print(f"  ✅ Docker信息采集完成")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"  ❌ 采集异常: {e}")
        finally:
            ssh.disconnect()
        
        return result
    
    def run_inspection(self, servers: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行批量巡检
        
        Args:
            servers: 服务器列表，默认使用config中的配置
            
        Returns:
            所有服务器的巡检结果
        """
        if servers is None:
            servers = config.SERVERS
        
        inspection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n{'='*70}")
        print(f"  Linux服务器批量自动化巡检")
        print(f"  巡检时间: {inspection_time}")
        print(f"{'='*70}")
        print(f"\n目标服务器数量: {len(servers)}")
        for s in servers:
            print(f"  • {s.get('name', s['host'])} ({s['host']}:{s['port']})")
        print()
        
        all_data = {}
        
        for i, server_config in enumerate(servers, 1):
            server_name = server_config.get('name', server_config['host'])
            print(f"\n[{i}/{len(servers)}] 正在巡检服务器: {server_name}")
            print('-' * 50)
            
            server_data = self.inspect_server(server_config)
            all_data[server_name] = server_data
            
            # 打印简要结果
            self._print_server_summary(server_data)
        
        return all_data
    
    def _print_server_summary(self, data: Dict[str, Any]):
        """打印单服务器巡检摘要"""
        if 'error' in data:
            print(f"  ⚠️  巡检失败: {data['error']}")
            return
        
        cpu = data.get('cpu', {})
        mem = data.get('memory', {})
        docker = data.get('docker_summary', {})
        
        print(f"\n  📊 巡检摘要:")
        print(f"     CPU: {cpu.get('cpu_usage', 0):.1f}% | 负载: {cpu.get('load_1min', 0):.2f}")
        print(f"     内存: {mem.get('usage_percent', 0):.1f}% ({mem.get('used_mb', 0)}/{mem.get('total_mb', 0)} MB)")
        
        disk = data.get('disk', [])
        if disk:
            max_usage = max(d.get('usage_percent', 0) for d in disk)
            print(f"     磁盘: 最高使用率 {max_usage}%")
        
        if docker.get('installed'):
            print(f"     Docker: {docker.get('containers_running', 0)}/{docker.get('containers_total', 0)} 容器运行中")
        else:
            print(f"     Docker: 未安装")
    
    def generate_pdf_report(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        生成PDF巡检报告
        
        Args:
            data: 巡检数据
            filename: 输出文件名
            
        Returns:
            生成的PDF文件路径
        """
        print(f"\n📄 正在生成PDF报告...")
        filepath = self.pdf_reporter.generate_report(data, filename)
        print(f"✅ PDF报告已生成: {filepath}")
        return filepath
    
    def generate_excel_report(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        生成Excel巡检报告
        
        Args:
            data: 巡检数据
            filename: 输出文件名
            
        Returns:
            生成的Excel文件路径
        """
        print(f"\n📊 正在生成Excel报告...")
        filepath = self.excel_reporter.generate_report(data, [], filename)
        print(f"✅ Excel报告已生成: {filepath}")
        return filepath


def main():
    parser = argparse.ArgumentParser(
        description='Linux服务器批量自动化巡检工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python inspection_with_pdf.py                    # 使用默认配置执行巡检
  python inspection_with_pdf.py --format pdf       # 只生成PDF报告
  python inspection_with_pdf.py --format excel     # 只生成Excel报告
  python inspection_with_pdf.py --format both      # 同时生成PDF和Excel报告
  python inspection_with_pdf.py --output ./reports # 指定输出目录
        """
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['pdf', 'excel', 'both'],
        default='both',
        help='报告格式 (默认: both)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='./reports',
        help='报告输出目录 (默认: ./reports)'
    )
    
    parser.add_argument(
        '--host',
        help='指定单个服务器IP (覆盖配置文件)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=22,
        help='SSH端口 (默认: 22)'
    )
    
    parser.add_argument(
        '--username', '-u',
        default='root',
        help='SSH用户名 (默认: root)'
    )
    
    parser.add_argument(
        '--key-file', '-k',
        help='SSH私钥文件路径'
    )
    
    args = parser.parse_args()
    
    # 设置输出目录
    if args.output:
        config.OUTPUT_DIR = args.output
        if not os.path.exists(config.OUTPUT_DIR):
            os.makedirs(config.OUTPUT_DIR)
    
    # 准备服务器列表
    servers = config.SERVERS.copy()
    
    # 如果指定了单个主机，覆盖配置
    if args.host:
        servers = [{
            'name': args.host,
            'host': args.host,
            'port': args.port,
            'username': args.username,
            'key_file': args.key_file
        }]
    
    # 创建巡检器并执行
    inspector = ServerInspector()
    
    try:
        # 执行巡检
        inspection_data = inspector.run_inspection(servers)
        
        # 生成报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if args.format in ['pdf', 'both']:
            pdf_file = inspector.generate_pdf_report(
                inspection_data,
                f"server_inspection_{timestamp}.pdf"
            )
        
        if args.format in ['excel', 'both']:
            excel_file = inspector.generate_excel_report(
                inspection_data,
                f"server_inspection_{timestamp}.xlsx"
            )
        
        # 打印最终摘要
        print(f"\n{'='*70}")
        print("  巡检完成!")
        print(f"{'='*70}")
        print(f"\n📁 报告输出目录: {os.path.abspath(config.OUTPUT_DIR)}")
        
        if args.format in ['pdf', 'both']:
            print(f"   📄 PDF报告: {pdf_file}")
        if args.format in ['excel', 'both']:
            print(f"   📊 Excel报告: {excel_file}")
        
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 巡检被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 巡检出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
