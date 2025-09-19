#!/usr/bin/env python3
"""
Pakistan Railway Booking Assistant
Advanced Train Booking System with AI Agent and Web Scraper

Author: AI Assistant
Date: 2025
"""

import sys
import os
from modules.ai_agent import TrainBookingAI
from modules.utils import DisplayManager, Logger
from modules.scraper import PakRailScraper
from config.settings import Config

class TrainBookingApp:
    def __init__(self):
        self.logger = Logger("TrainBookingApp")
        self.display = DisplayManager()
        self.ai_agent = TrainBookingAI()
        self.config = Config()
        
        # Check configuration
        self.check_config()
    
    def check_config(self):
        """Check if all required configurations are present"""
        if not self.config.OPENROUTER_API_KEY:
            self.logger.error("OPENROUTER_API_KEY environment variable nahi mila!")
            self.logger.error("Please .env file mein API key set kariye:")
            self.logger.error("OPENROUTER_API_KEY=your_api_key_here")
            sys.exit(1)
        
        self.logger.info("Configuration check passed!")
    
    def display_menu(self):
        """Display main menu options"""
        menu = """
╔══════════════════════════════════════════════════════════════╗
║                    🚂 MAIN MENU 🚂                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. 💬 AI Assistant se baat kariye                          ║
║  2. 🔍 Direct Train Search (Manual)                         ║
║  3. 📊 Saved Train Data dekhiye                             ║
║  4. ⚙️  System Information                                   ║
║  5. ❌ Exit                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Aap kya karna chahte hain? (1-5): """
        
        return input(menu).strip()
    
    def run_ai_assistant(self):
        """Run the interactive AI assistant"""
        self.display.console.print("\n[bold green]🤖 AI Assistant se baat shuru kariye![/bold green]")
        self.display.console.print("[yellow]'exit', 'quit' ya 'bye' type kariye khatam karne ke liye[/yellow]\n")
        
        while True:
            try:
                user_input = input("🗣️  Aap: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'khatam']:
                    self.display.console.print("\n[green]Dhanyawad! Phir milenge! 👋[/green]")
                    break
                
                if not user_input:
                    continue
                
                # Show typing indicator
                self.display.console.print("[dim]🤔 AI soch raha hai...[/dim]")
                
                # Get AI response
                response = self.ai_agent.process_user_input(user_input)
                
                # Display response
                self.display.console.print(f"\n🤖 [bold blue]AI Assistant:[/bold blue] {response}\n")
                
            except KeyboardInterrupt:
                self.display.console.print("\n\n[yellow]Conversation interrupted. Main menu par ja rahe hain...[/yellow]")
                break
            except Exception as e:
                self.logger.error(f"AI Assistant mein error: {str(e)}")
                self.display.console.print("\n[red]Kuch technical issue hai. Please try again.[/red]\n")
    
    def run_manual_search(self):
        """Run manual train search"""
        self.display.console.print("\n[bold blue]🔍 Manual Train Search[/bold blue]")
        
        try:
            # Get user inputs
            from_station = input("📍 From Station: ").strip()
            to_station = input("📍 To Station: ").strip()
            travel_date = input("📅 Travel Date (YYYY-MM-DD): ").strip()
            
            if not all([from_station, to_station, travel_date]):
                self.display.console.print("[red]Saari fields fill kariye![/red]")
                return
            
            # Validate date format
            try:
                from datetime import datetime
                datetime.strptime(travel_date, '%Y-%m-%d')
            except ValueError:
                self.display.console.print("[red]Date format galat hai! YYYY-MM-DD use kariye[/red]")
                return
            
            self.display.console.print(f"\n[yellow]🔍 Searching trains from {from_station} to {to_station} on {travel_date}...[/yellow]")
            
            # Start scraping
            scraper = PakRailScraper()
            trains_data = scraper.scrape_train_info(from_station, to_station, travel_date)
            
            # Display results
            if trains_data:
                self.display.display_train_results(trains_data)
                self.display.console.print(f"\n[green]✅ Total {len(trains_data)} trains found![/green]")
            else:
                self.display.console.print("[red]❌ Koi trains nahi mili![/red]")
                
        except Exception as e:
            self.logger.error(f"Manual search mein error: {str(e)}")
            self.display.console.print("[red]Search mein kuch error aa gaya![/red]")
    
    def show_saved_data(self):
        """Show previously saved train data"""
        try:
            from modules.utils import DataManager
            saved_data = DataManager.load_train_data()
            
            if saved_data:
                self.display.console.print(f"\n[green]📊 {len(saved_data)} saved trains found:[/green]")
                self.display.display_train_results(saved_data)
            else:
                self.display.console.print("\n[yellow]📊 Koi saved data nahi hai![/yellow]")
                
        except Exception as e:
            self.logger.error(f"Saved data show karne mein error: {str(e)}")
            self.display.console.print("[red]Saved data access nahi ho saka![/red]")
    
    def show_system_info(self):
        """Show system information"""
        self.display.console.print("\n[bold blue]⚙️ System Information[/bold blue]")
        
        info_table = f"""
╔══════════════════════════════════════════════════════════════╗
║                   📋 SYSTEM INFO 📋                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🐍 Python Version: {sys.version.split()[0]}                                ║
║  📁 Current Directory: {os.getcwd()[:40]}...                ║
║  🔑 API Key: {'✅ Set' if self.config.OPENROUTER_API_KEY else '❌ Missing'}                                     ║
║  🌐 Target Website: {self.config.PAKRAIL_URL}               ║
║  🤖 AI Model: {self.config.AI_MODEL}                        ║
║  ⏱️  Selenium Timeout: {self.config.SELENIUM_TIMEOUT}s                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(info_table)
    
    def run(self):
        """Main application loop"""
        try:
            # Display welcome message
            self.display.display_welcome()
            
            while True:
                try:
                    choice = self.display_menu()
                    
                    if choice == '1':
                        self.run_ai_assistant()
                    elif choice == '2':
                        self.run_manual_search()
                    elif choice == '3':
                        self.show_saved_data()
                    elif choice == '4':
                        self.show_system_info()
                    elif choice == '5':
                        self.display.console.print("\n[green]Dhanyawad! Allah hafiz! 👋[/green]")
                        break
                    else:
                        self.display.console.print("\n[red]Galat choice! 1-5 mein se select kariye.[/red]")
                    
                    # Pause before showing menu again
                    input("\nPress Enter to continue...")
                    
                except KeyboardInterrupt:
                    self.display.console.print("\n\n[yellow]Application band kar rahe hain...[/yellow]")
                    break
                except Exception as e:
                    self.logger.error(f"Menu handling mein error: {str(e)}")
                    self.display.console.print("\n[red]Kuch error aa gaya! Please try again.[/red]")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Application main loop mein error: {str(e)}")
            self.display.console.print("[red]Critical error! Application band ho raha hai.[/red]")
        
        finally:
            # Cleanup
            if hasattr(self.ai_agent, 'scraper') and self.ai_agent.scraper:
                self.ai_agent.scraper.cleanup()

def main():
    """Application entry point"""
    try:
        app = TrainBookingApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\nCritical error: {str(e)}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()