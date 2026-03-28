import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import config


class PDFReporter:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or config.OUTPUT_DIR
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.font_name = self._setup_fonts()
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        
    def _setup_fonts(self):
        font_name = 'Helvetica'
        
        font_paths = []
        if sys.platform.startswith('win'):
            font_paths = [
                'C:/Windows/Fonts/simsun.ttc',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simhei.ttf',
            ]
        elif sys.platform.startswith('darwin'):
            font_paths = [
                '/Library/Fonts/Songti.ttc',
                '/Library/Fonts/PingFang.ttc',
            ]
        else:
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_base = os.path.splitext(os.path.basename(font_path))[0]
                    pdfmetrics.registerFont(TTFont(font_base, font_path))
                    font_name = font_base
                    break
                except:
                    continue
        
        return font_name
        
    def _setup_styles(self):
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontName=self.font_name,
            fontSize=16,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50')
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontName=self.font_name,
            fontSize=12,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#34495e')
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=9,
            spaceAfter=6
        )
        
    def _get_table_style(self, header_color: str):
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
    
    def _create_summary_section(self, data: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("一、巡检概览", self.heading_style))
        
        table_data = [
            ['服务器', 'IP地址', '巡检时间', '系统', '运行时间', 
             'CPU负载', 'CPU使用率', '内存使用率', 
             'Docker状态', '容器运行数']
        ]
        
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
            
            table_data.append([
                server_name,
                sys_info.get('host', ''),
                inspection_time,
                sys_info.get('os', ''),
                sys_info.get('uptime', ''),
                cpu_load,
                cpu_usage,
                mem_usage,
                docker_status,
                str(docker_info.get('containers_running', 0))
            ])
        
        col_widths = [2*cm, 2.5*cm, 3*cm, 3*cm, 2*cm, 2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(self._get_table_style('#3498db'))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_disk_section(self, data: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("二、磁盘信息", self.heading_style))
        
        table_data = [
            ['服务器', '文件系统', '总容量', '已使用', '可用', '使用率', '挂载点']
        ]
        
        for server_name, server_data in data.items():
            disk_info = server_data.get('disk', [])
            for disk in disk_info:
                usage = disk.get('usage_percent', 0)
                table_data.append([
                    server_name,
                    disk.get('filesystem', ''),
                    disk.get('size', ''),
                    disk.get('used', ''),
                    disk.get('available', ''),
                    f"{usage}%",
                    disk.get('mount_point', '')
                ])
        
        col_widths = [2.5*cm, 3*cm, 2*cm, 2*cm, 2*cm, 1.5*cm, 3*cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(self._get_table_style('#27ae60'))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_port_section(self, data: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("三、端口监听状态", self.heading_style))
        
        table_data = [
            ['服务器', '端口', '状态', '服务程序']
        ]
        
        for server_name, server_data in data.items():
            port_info = server_data.get('listening_ports', [])
            for port in port_info:
                table_data.append([
                    server_name,
                    str(port.get('port', '')),
                    'LISTENING',
                    port.get('program', '')
                ])
        
        col_widths = [4*cm, 2*cm, 2.5*cm, 6*cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(self._get_table_style('#f39c12'))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_process_section(self, data: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("四、系统进程存活情况", self.heading_style))
        
        table_data = [
            ['服务器', '进程名', '状态', '实例数', 'PID列表']
        ]
        
        for server_name, server_data in data.items():
            process_info = server_data.get('processes', [])
            for proc in process_info:
                table_data.append([
                    server_name,
                    proc.get('name', ''),
                    proc.get('status', ''),
                    str(proc.get('count', 0)),
                    proc.get('pids', '')
                ])
        
        col_widths = [3*cm, 2.5*cm, 2*cm, 2*cm, 5*cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(self._get_table_style('#9b59b6'))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_docker_container_section(self, data: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("五、Docker容器信息", self.heading_style))
        
        table_data = [
            ['服务器', '容器ID', '容器名', '镜像', '状态', '端口映射', '运行状态']
        ]
        
        for server_name, server_data in data.items():
            containers = server_data.get('containers', [])
            for container in containers:
                table_data.append([
                    server_name,
                    container.get('id', ''),
                    container.get('name', ''),
                    container.get('image', ''),
                    container.get('status', ''),
                    container.get('ports', ''),
                    container.get('state', '')
                ])
        
        col_widths = [2*cm, 1.8*cm, 2.5*cm, 3*cm, 3*cm, 3*cm, 2*cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(self._get_table_style('#34495e'))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_docker_image_section(self, data: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("六、Docker镜像信息", self.heading_style))
        
        table_data = [
            ['服务器', '仓库', '标签', '镜像ID', '大小', '创建时间']
        ]
        
        for server_name, server_data in data.items():
            images = server_data.get('images', [])
            for image in images:
                table_data.append([
                    server_name,
                    image.get('repository', ''),
                    image.get('tag', ''),
                    image.get('id', ''),
                    image.get('size', ''),
                    image.get('created', '')
                ])
        
        col_widths = [2*cm, 4*cm, 2*cm, 2*cm, 2*cm, 4*cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(self._get_table_style('#1abc9c'))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def generate_report(self, data: Dict[str, Any], history_data: List[Dict[str, Any]] = None, 
                       filename: str = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"inspection_report_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        elements = []
        
        title = Paragraph("Linux服务器自动化巡检报告", self.title_style)
        elements.append(title)
        
        report_time = Paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style)
        elements.append(report_time)
        elements.append(Spacer(1, 0.5*cm))
        
        elements.extend(self._create_summary_section(data))
        elements.extend(self._create_disk_section(data))
        elements.extend(self._create_port_section(data))
        elements.extend(self._create_process_section(data))
        elements.extend(self._create_docker_container_section(data))
        elements.extend(self._create_docker_image_section(data))
        
        doc.build(elements)
        
        return filepath
    
    def update_report(self, filepath: str, data: Dict[str, Any], history_data: List[Dict[str, Any]]):
        return self.generate_report(data, history_data, os.path.basename(filepath))
