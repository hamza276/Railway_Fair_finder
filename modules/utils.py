import json
import logging
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import colorama
from colorama import Fore, Style

colorama.init()

class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message):
        self.logger.info(f"{Fore.GREEN}INFO: {message}{Style.RESET_ALL}")
    
    def error(self, message):
        self.logger.error(f"{Fore.RED}ERROR: {message}{Style.RESET_ALL}")
    
    def warning(self, message):
        self.logger.warning(f"{Fore.YELLOW}WARNING: {message}{Style.RESET_ALL}")

class DataManager:
    @staticmethod
    def save_train_data(data, filename="data/train_data.json"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_train_data(filename="data/train_data.json"):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

class DisplayManager:
    def __init__(self):
        self.console = Console()
    
    def display_welcome(self):
        welcome_text = """
        🚂 PAKISTAN RAILWAY BOOKING ASSISTANT 🚂
        
        Aapka swagat hai! Main aapki train booking mein madad karunga.
        """
        
        panel = Panel.fit(
            welcome_text,
            border_style="bright_blue",
            title="Welcome"
        )
        self.console.print(panel)
    
    def display_train_results(self, trains_data):
        if not trains_data:
            self.console.print("[red]Koi train data nahi mila![/red]")
            return
        
        table = Table(title="🚂 Train Information")
        table.add_column("Train Name", style="cyan")
        table.add_column("Route", style="magenta")
        table.add_column("Departure", style="green")
        table.add_column("Arrival", style="green")
        table.add_column("Economy", style="yellow")
        table.add_column("Business", style="yellow")
        table.add_column("AC", style="yellow")
        table.add_column("Stops", style="blue")
        
        for train in trains_data:
            table.add_row(
                train.get('name', 'N/A'),
                train.get('route', 'N/A'),
                train.get('departure_time', 'N/A'),
                train.get('arrival_time', 'N/A'),
                train.get('economy_fare', 'N/A'),
                train.get('business_fare', 'N/A'),
                train.get('ac_fare', 'N/A'),
                train.get('stops', 'N/A')
            )
        
        self.console.print(table)