import os
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
import config


class PDFReporter:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or config.OUTPUT_DIR
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a5276'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2874a6'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        self.heading3_style = ParagraphStyle(
            'CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#3498db'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT
        )
        
        self.center_style = ParagraphStyle(
            'CenterStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER
        )
        
        self.warning_style = ParagraphStyle(
            'WarningStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.orange,
            fontName='Helvetica-Bold'
        )
        
        self.danger_style = ParagraphStyle(
            'DangerStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            fontName='Helvetica-Bold'
        )
        
        self.success_style = ParagraphStyle(
            'SuccessStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.green,
            fontName='Helvetica-Bold'
        )
    
    def _get_status_color(self, value: float, warning: float = 60, danger: float = 80) -> colors.Color:
        if value >= danger:
            return colors.HexColor('#e74c3c')
        elif value >= warning:
            return colors.HexColor('#f39c12')
        return colors.HexColor('#27ae60')
    
    def _create_table_style(self, header_color: colors.Color = colors.HexColor('#3498db')) -> TableStyle:
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8f9fa')]),
        ])
    
    def _create_cover_page(self, story: List, data: Dict[str, Any]):
        story.append(Spacer(1, 100))
        
        title = Paragraph("Linux服务器巡检报告", self.title_style)
        story.append(title)
        
        story.append(Spacer(1, 50))
        
        timestamp = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        info_data = [
            ['报告生成时间', timestamp],
            ['巡检服务器数量', str(len(data))],
            ['报告类型', '自动化巡检'],
        ]
        
        info_table = Table(info_data, colWidths=[150, 250])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(info_table)
        
        story.append(Spacer(1, 30))
        
        server_list = []
        for server_name in data.keys():
            server_list.append([server_name])
        
        if server_list:
            server_table = Table([['服务器列表']] + server_list, colWidths=[400])
            server_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(server_table)
        
        story.append(PageBreak())
    
    def _create_summary_section(self, story: List, data: Dict[str, Any]):
        story.append(Paragraph("巡检概览", self.heading2_style))
        story.append(Spacer(1, 10))
        
        headers = ['服务器', 'IP地址', '巡检时间', '系统', '运行时间', 
                   'CPU负载(1/5/15min)', 'CPU使用率', '内存使用率', 
                   'Docker状态', '容器运行数']
        
        table_data = [headers]
        
        for server_name, server_data in data.items():
            sys_info = server_data.get('system', {})
            cpu_info = server_data.get('cpu', {})
            mem_info = server_data.get('memory', {})
            docker_info = server_data.get('docker_summary', {})
            inspection_time = server_data.get('inspection_time', '')
            
            cpu_load = f"{cpu_info.get('load_1min', 0):.2f}/{cpu_info.get('load_5min', 0):.2f}/{cpu_info.get('load_15min', 0):.2f}"
            cpu_usage = f"{cpu_info.get('cpu_usage', 0):.1f}%"
            mem_usage = f"{mem_info.get('usage_percent', 0):.1f}%"
            docker_status = "运行中" if docker_info.get('running', False) else "未运行"
            containers = str(docker_info.get('containers_running', 0))
            
            row = [
                server_name,
                sys_info.get('host', ''),
                inspection_time,
                sys_info.get('os', '')[:30],
                sys_info.get('uptime', '')[:20],
                cpu_load,
                cpu_usage,
                mem_usage,
                docker_status,
                containers
            ]
            table_data.append(row)
        
        col_widths = [80, 90, 100, 100, 70, 90, 60, 60, 60, 50]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        style = self._create_table_style()
        
        for i, row in enumerate(table_data[1:], start=1):
            cpu_str = row[6].replace('%', '')
            mem_str = row[7].replace('%', '')
            try:
                cpu_val = float(cpu_str)
                mem_val = float(mem_str)
                
                cpu_color = self._get_status_color(cpu_val)
                mem_color = self._get_status_color(mem_val)
                
                style.add('BACKGROUND', (6, i), (6, i), cpu_color)
                style.add('TEXTCOLOR', (6, i), (6, i), colors.whitesmoke if cpu_val >= 60 else colors.black)
                
                style.add('BACKGROUND', (7, i), (7, i), mem_color)
                style.add('TEXTCOLOR', (7, i), (7, i), colors.whitesmoke if mem_val >= 60 else colors.black)
            except ValueError:
                pass
        
        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 20))
    
    def _create_cpu_section(self, story: List, data: Dict[str, Any]):
        story.append(Paragraph("CPU 详细信息", self.heading2_style))
        story.append(Spacer(1, 10))
        
        for server_name, server_data in data.items():
            cpu_info = server_data.get('cpu', {})
            
            story.append(Paragraph(f"服务器: {server_name}", self.heading3_style))
            
            cpu_data = [
                ['指标', '数值'],
                ['CPU核心数', str(cpu_info.get('cpu_cores', 0))],
                ['CPU使用率', f"{cpu_info.get('cpu_usage', 0):.2f}%"],
                ['1分钟负载', f"{cpu_info.get('load_1min', 0):.2f}"],
                ['5分钟负载', f"{cpu_info.get('load_5min', 0):.2f}"],
                ['15分钟负载', f"{cpu_info.get('load_15min', 0):.2f}"],
            ]
            
            table = Table(cpu_data, colWidths=[150, 150])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ])
            
            cpu_usage = cpu_info.get('cpu_usage', 0)
            usage_color = self._get_status_color(cpu_usage)
            style.add('BACKGROUND', (1, 2), (1, 2), usage_color)
            style.add('TEXTCOLOR', (1, 2), (1, 2), colors.whitesmoke if cpu_usage >= 60 else colors.black)
            
            table.setStyle(style)
            story.append(table)
            story.append(Spacer(1, 10))
        
        story.append(PageBreak())
    
    def _create_memory_section(self, story: List, data: Dict[str, Any]):
        story.append(Paragraph("内存 详细信息", self.heading2_style))
        story.append(Spacer(1, 10))
        
        for server_name, server_data in data.items():
            mem_info = server_data.get('memory', {})
            
            story.append(Paragraph(f"服务器: {server_name}", self.heading3_style))
            
            total = mem_info.get('total_mb', 0)
            used = mem_info.get('used_mb', 0)
            free = mem_info.get('free_mb', 0)
            available = mem_info.get('available_mb', 0)
            usage = mem_info.get('usage_percent', 0)
            
            mem_data = [
                ['指标', '数值 (MB)', '百分比'],
                ['总内存', str(total), '100%'],
                ['已使用', str(used), f"{usage:.2f}%"],
                ['空闲', str(free), f"{(free/total*100):.2f}%" if total > 0 else '0%'],
                ['可用', str(available), f"{(available/total*100):.2f}%" if total > 0 else '0%'],
            ]
            
            table = Table(mem_data, colWidths=[120, 120, 100])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ])
            
            usage_color = self._get_status_color(usage)
            style.add('BACKGROUND', (1, 2), (2, 2), usage_color)
            style.add('TEXTCOLOR', (1, 2), (2, 2), colors.whitesmoke if usage >= 60 else colors.black)
            
            table.setStyle(style)
            story.append(table)
            story.append(Spacer(1, 10))
        
        story.append(PageBreak())
    
    def _create_disk_section(self, story: List, data: Dict[str, Any]):
        story.append(Paragraph("磁盘 详细信息", self.heading2_style))
        story.append(Spacer(1, 10))
        
        for server_name, server_data in data.items():
            disk_info = server_data.get('disk', [])
            
            if not disk_info:
                continue
            
            story.append(Paragraph(f"服务器: {server_name}", self.heading3_style))
            
            disk_data = [['文件系统', '总容量', '已使用', '可用', '使用率', '挂载点']]
            
            for disk in disk_info:
                row = [
                    disk.get('filesystem', '')[:25],
                    disk.get('size', ''),
                    disk.get('used', ''),
                    disk.get('available', ''),
                    f"{disk.get('usage_percent', 0)}%",
                    disk.get('mount_point', '')
                ]
                disk_data.append(row)
            
            col_widths = [100, 60, 60, 60, 50, 80]
            table = Table(disk_data, colWidths=col_widths, repeatRows=1)
            style = self._create_table_style(colors.HexColor('#e67e22'))
            
            for i, disk in enumerate(disk_info, start=1):
                usage = disk.get('usage_percent', 0)
                usage_color = self._get_status_color(usage)
                style.add('BACKGROUND', (4, i), (4, i), usage_color)
                style.add('TEXTCOLOR', (4, i), (4, i), colors.whitesmoke if usage >= 60 else colors.black)
            
            table.setStyle(style)
            story.append(table)
            story.append(Spacer(1, 15))
        
        story.append(PageBreak())
    
    def _create_port_section(self, story: List, data: Dict[str, Any]):
        story.append(Paragraph("TCP端口监听状态", self.heading2_style))
        story.append(Spacer(1, 10))
        
        for server_name, server_data in data.items():
            ports = server_data.get('ports', [])
            listening_ports = server_data.get('listening_ports', [])
            
            story.append(Paragraph(f"服务器: {server_name}", self.heading3_style))
            
            story.append(Paragraph("关键端口检查:", self.normal_style))
            port_data = [['端口', '状态']]
            for port in ports:
                status = '✓ 监听中' if port.get('is_listening', False) else '✗ 未监听'
                port_data.append([str(port.get('port', '')), status])
            
            table = Table(port_data, colWidths=[100, 150])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1abc9c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            
            for i in range(1, len(port_data)):
                is_listening = '✓' in port_data[i][1]
                if is_listening:
                    style.add('BACKGROUND', (1, i), (1, i), colors.HexColor('#d5f4e6'))
                    style.add('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#27ae60'))
                else:
                    style.add('BACKGROUND', (1, i), (1, i), colors.HexColor('#fadbd8'))
                    style.add('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#e74c3c'))
            
            table.setStyle(style)
            story.append(table)
            story.append(Spacer(1, 10))
            
            if listening_ports:
                story.append(Paragraph("所有监听端口:", self.normal_style))
                listen_data = [['端口', '地址', '程序']]
                for port_info in listening_ports[:20]:
                    listen_data.append([
                        str(port_info.get('port', '')),
                        port_info.get('address', ''),
                        port_info.get('program', '-')[:25]
                    ])
                
                if len(listening_ports) > 20:
                    listen_data.append(['...', f'共 {len(listening_ports)} 个端口', '...'])
                
                listen_table = Table(listen_data, colWidths=[60, 120, 150], repeatRows=1)
                listen_table.setStyle(self._create_table_style(colors.HexColor('#16a085')))
                story.append(listen_table)
            
            story.append(Spacer(1, 15))
        
        story.append(PageBreak())
    
    def _create_process_section(self, story: List, data: Dict[str, Any]):
        story.append(Paragraph("系统进程状态", self.heading2_style))
        story.append(Spacer(1, 10))
        
        for server_name, server_data in data.items():
            processes = server_data.get('processes', [])
            
            story.append(Paragraph(f"服务器: {server_name}", self.heading3_style))
            
            proc_data = [['进程名', '状态', '实例数', 'PID列表']]
            for proc in processes:
                proc_data.append([
                    proc.get('name', ''),
                    '运行中' if proc.get('is_running', False) else '未运行',
                    str(proc.get('count', 0)),
                    proc.get('pids', '-')[:30]
                ])
            
            table = Table(proc_data, colWidths=[100, 80, 60, 150], repeatRows=1)
            style = self._create_table_style(colors.HexColor('#8e44ad'))
            
            for i, proc in enumerate(processes, start=1):
                if proc.get('is_running', False):
                    style.add('BACKGROUND', (1, i), (1, i), colors.HexColor('#d5f4e6'))
                    style.add('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#27ae60'))
                else:
                    style.add('BACKGROUND', (1, i), (1, i), colors.HexColor('#fadbd8'))
                    style.add('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#e74c3c'))
            
            table.setStyle(style)
            story.append(table)
            story.append(Spacer(1, 15))
        
        story.append(PageBreak())
    
    def _create_docker_section(self, story: List, data: Dict[str, Any]):
        story.append(Paragraph("Docker 信息", self.heading2_style))
        story.append(Spacer(1, 10))
        
        for server_name, server_data in data.items():
            docker_summary = server_data.get('docker_summary', {})
            containers = server_data.get('containers', [])
            images = server_data.get('images', [])
            
            story.append(Paragraph(f"服务器: {server_name}", self.heading3_style))
            
            if not docker_summary.get('installed', False):
                story.append(Paragraph("Docker 未安装", self.normal_style))
                story.append(Spacer(1, 15))
                continue
            
            docker_data = [
                ['属性', '值'],
                ['Docker版本', docker_summary.get('version', '未知')],
                ['运行状态', '运行中' if docker_summary.get('running', False) else '已停止'],
                ['存储驱动', docker_summary.get('storage_driver', '未知')],
                ['Docker根目录', docker_summary.get('docker_root_dir', '未知')],
                ['容器总数', str(docker_summary.get('containers_total', 0))],
                ['运行中容器', str(docker_summary.get('containers_running', 0))],
                ['已停止容器', str(docker_summary.get('containers_stopped', 0))],
                ['镜像数量', str(docker_summary.get('images_count', 0))],
            ]
            
            table = Table(docker_data, colWidths=[150, 300])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ])
            
            running = docker_summary.get('running', False)
            if running:
                style.add('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#d5f4e6'))
                style.add('TEXTCOLOR', (1, 2), (1, 2), colors.HexColor('#27ae60'))
            else:
                style.add('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#fadbd8'))
                style.add('TEXTCOLOR', (1, 2), (1, 2), colors.HexColor('#e74c3c'))
            
            table.setStyle(style)
            story.append(table)
            story.append(Spacer(1, 15))
            
            if containers:
                story.append(Paragraph("容器列表:", self.normal_style))
                container_data = [['容器ID', '名称', '镜像', '状态', '运行状态']]
                for container in containers:
                    container_data.append([
                        container.get('id', '')[:12],
                        container.get('name', '')[:20],
                        container.get('image', '')[:25],
                        container.get('status', '')[:30],
                        container.get('state', '')
                    ])
                
                container_table = Table(container_data, colWidths=[70, 100, 120, 120, 60], repeatRows=1)
                container_style = self._create_table_style(colors.HexColor('#2980b9'))
                
                for i, container in enumerate(containers, start=1):
                    if container.get('is_running', False):
                        container_style.add('BACKGROUND', (4, i), (4, i), colors.HexColor('#d5f4e6'))
                        container_style.add('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#27ae60'))
                    else:
                        container_style.add('BACKGROUND', (4, i), (4, i), colors.HexColor('#fadbd8'))
                        container_style.add('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#e74c3c'))
                
                container_table.setStyle(container_style)
                story.append(container_table)
                story.append(Spacer(1, 10))
            
            if images:
                story.append(Paragraph(f"镜像列表 (共 {len(images)} 个):", self.normal_style))
                image_data = [['仓库', '标签', '镜像ID', '大小']]
                for image in images[:15]:
                    image_data.append([
                        image.get('repository', '')[:25],
                        image.get('tag', '')[:15],
                        image.get('id', '')[:12],
                        image.get('size', '')
                    ])
                
                if len(images) > 15:
                    image_data.append(['...', '...', f'还有 {len(images) - 15} 个镜像', '...'])
                
                image_table = Table(image_data, colWidths=[150, 80, 100, 80], repeatRows=1)
                image_table.setStyle(self._create_table_style(colors.HexColor('#27ae60')))
                story.append(image_table)
            
            story.append(Spacer(1, 20))
        
        story.append(PageBreak())
    
    def generate_report(self, data: Dict[str, Any], filename: str = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"inspection_report_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        self._create_cover_page(story, data)
        self._create_summary_section(story, data)
        self._create_cpu_section(story, data)
        self._create_memory_section(story, data)
        self._create_disk_section(story, data)
        self._create_port_section(story, data)
        self._create_process_section(story, data)
        self._create_docker_section(story, data)
        
        doc.build(story)
        
        return filepath
