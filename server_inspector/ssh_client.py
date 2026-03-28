import paramiko
from typing import Optional, Tuple
import socket


class SSHClient:
    def __init__(self, host: str, port: int, username: str, key_path: Optional[str] = None, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.key_path = key_path
        self.password = password
        self.client: Optional[paramiko.SSHClient] = None

    def connect(self) -> bool:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_path:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=30
                )
            else:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30
                )
            return True
        except Exception as e:
            print(f"SSH连接失败 [{self.host}]: {e}")
            return False

    def execute(self, command: str) -> Tuple[int, str, str]:
        if not self.client:
            return -1, "", "SSH未连接"
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=60)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            return exit_code, output, error
        except socket.timeout:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
