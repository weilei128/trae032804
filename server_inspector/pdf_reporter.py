from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from typing import List, Dict
import os

from system_collector import CPUInfo, MemoryInfo, DiskInfo, PortInfo, ProcessInfo
from docker_collector import DockerInfo


class PDFReporter:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_chinese_font()
        self._setup_styles()

    def _setup_chinese_font(self):
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/PingFang.ttc"
        ]
        
        self.chinese_font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    self.chinese_font = 'ChineseFont'
                    break
                except:
                    continue
        
        if not self.chinese_font:
            self.chinese_font = 'Helvetica'

    def _setup_styles(self):
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.chinese_font,
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontName=self.chinese_font,
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=10
        )

    def generate_report(self, server_data: List[Dict]):
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        elements.append(Paragraph("Linux Server Inspection Report", self.title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        elements.append(Spacer(1, 20))
        
        for idx, data in enumerate(server_data, 1):
            elements.extend(self._generate_server_section(data, idx))
            if idx < len(server_data):
                elements.append(PageBreak())
        
        doc.build(elements)
        return self.output_path

    def _generate_server_section(self, data: Dict, index: int) -> List:
        elements = []
        
        server_title = f"Server {index}: {data['host']} ({data.get('hostname', 'N/A')})"
        elements.append(Paragraph(server_title, self.heading_style))
        
        elements.extend(self._generate_system_info(data))
        elements.extend(self._generate_cpu_info(data.get('cpu')))
        elements.extend(self._generate_memory_info(data.get('memory')))
        elements.extend(self._generate_disk_info(data.get('disks', [])))
        elements.extend(self._generate_port_info(data.get('ports', [])))
        elements.extend(self._generate_process_info(data.get('processes', [])))
        elements.extend(self._generate_docker_info(data.get('docker')))
        
        return elements

    def _generate_system_info(self, data: Dict) -> List:
        elements = []
        elements.append(Paragraph("System Information", self.heading_style))
        
        sys_data = [
            ['IP Address', data['host']],
            ['Hostname', data.get('hostname', 'N/A')],
            ['OS', data.get('os', 'N/A')],
            ['Kernel', data.get('kernel', 'N/A')],
            ['Uptime', data.get('uptime', 'N/A')]
        ]
        
        table = Table(sys_data, colWidths=[4*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        return elements

    def _generate_cpu_info(self, cpu: CPUInfo) -> List:
        elements = []
        if not cpu:
            return elements
            
        elements.append(Paragraph("CPU Information", self.heading_style))
        
        load_status = "Normal"
        if cpu.load_1min > cpu.cpu_cores:
            load_status = "High Load"
        elif cpu.load_1min > cpu.cpu_cores * 0.7:
            load_status = "Medium Load"
        
        cpu_data = [
            ['Metric', 'Value', 'Status'],
            ['CPU Cores', str(cpu.cpu_cores), '-'],
            ['1-min Load', f"{cpu.load_1min:.2f}", load_status],
            ['5-min Load', f"{cpu.load_5min:.2f}", '-'],
            ['15-min Load', f"{cpu.load_15min:.2f}", '-'],
            ['CPU Usage', f"{cpu.usage_percent}%", 'High' if cpu.usage_percent > 80 else 'Normal']
        ]
        
        table = Table(cpu_data, colWidths=[4*cm, 5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        return elements

    def _generate_memory_info(self, memory: MemoryInfo) -> List:
        elements = []
        if not memory:
            return elements
            
        elements.append(Paragraph("Memory Information", self.heading_style))
        
        mem_status = "Normal"
        if memory.usage_percent > 90:
            mem_status = "Critical"
        elif memory.usage_percent > 80:
            mem_status = "Warning"
        
        mem_data = [
            ['Metric', 'Value', 'Status'],
            ['Total Memory', f"{memory.total_mb:.2f} MB", '-'],
            ['Used Memory', f"{memory.used_mb:.2f} MB", '-'],
            ['Free Memory', f"{memory.free_mb:.2f} MB", '-'],
            ['Usage', f"{memory.usage_percent}%", mem_status]
        ]
        
        table = Table(mem_data, colWidths=[4*cm, 5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        return elements

    def _generate_disk_info(self, disks: List[DiskInfo]) -> List:
        elements = []
        if not disks:
            return elements
            
        elements.append(Paragraph("Disk Information", self.heading_style))
        
        disk_data = [['Filesystem', 'Total', 'Used', 'Available', 'Usage', 'Mount Point']]
        
        for disk in disks:
            usage_status = f"{disk.usage_percent}%"
            if disk.usage_percent > 90:
                usage_status += " (Critical)"
            elif disk.usage_percent > 80:
                usage_status += " (Warning)"
            
            disk_data.append([
                disk.filesystem[:20],
                f"{disk.total_gb:.2f} GB",
                f"{disk.used_gb:.2f} GB",
                f"{disk.available_gb:.2f} GB",
                usage_status,
                disk.mount_point[:15]
            ])
        
        table = Table(disk_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        return elements

    def _generate_port_info(self, ports: List[PortInfo]) -> List:
        elements = []
        if not ports:
            return elements
            
        elements.append(Paragraph("TCP Port Status", self.heading_style))
        
        port_data = [['Port', 'Protocol', 'Service', 'Status']]
        
        for port in ports:
            status_color = colors.green if port.state == "LISTENING" else colors.red
            port_data.append([
                str(port.port),
                port.protocol,
                port.service,
                port.state
            ])
        
        table = Table(port_data, colWidths=[3*cm, 3*cm, 4*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        return elements

    def _generate_process_info(self, processes: List[ProcessInfo]) -> List:
        elements = []
        if not processes:
            return elements
            
        elements.append(Paragraph("Process Status", self.heading_style))
        
        proc_data = [['PID', 'Name', 'Status']]
        
        for proc in processes:
            proc_data.append([
                str(proc.pid),
                proc.name,
                proc.status
            ])
        
        table = Table(proc_data, colWidths=[3*cm, 5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        return elements

    def _generate_docker_info(self, docker: DockerInfo) -> List:
        elements = []
        if not docker:
            return elements
            
        elements.append(Paragraph("Docker Information", self.heading_style))
        
        if not docker.installed:
            elements.append(Paragraph("Docker is not installed on this server.", self.normal_style))
            return elements
        
        summary_data = [
            ['Docker Version', docker.version],
            ['Running Containers', str(docker.running_containers)],
            ['Total Containers', str(docker.total_containers)],
            ['Total Images', str(docker.total_images)]
        ]
        
        table = Table(summary_data, colWidths=[4*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        if docker.containers:
            elements.append(Paragraph("Container List", self.normal_style))
            container_data = [['ID', 'Name', 'Image', 'State', 'Status']]
            
            for c in docker.containers[:10]:
                container_data.append([
                    c.container_id[:12],
                    c.name[:20],
                    c.image[:25],
                    c.state,
                    c.status[:20]
                ])
            
            table = Table(container_data, colWidths=[2.5*cm, 3*cm, 3.5*cm, 2*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 10))
        
        if docker.images:
            elements.append(Paragraph("Image List", self.normal_style))
            image_data = [['Repository', 'Tag', 'ID', 'Size']]
            
            for img in docker.images[:10]:
                image_data.append([
                    img.repository[:20],
                    img.tag[:15],
                    img.image_id[:12],
                    img.size
                ])
            
            table = Table(image_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
        
        return elements
