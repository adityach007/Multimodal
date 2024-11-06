import subprocess
import os
import webbrowser
from typing import Dict, Any

class CommandHandler:
    """Handles execution of various system commands."""
    
    COMMAND_CATEGORIES = {
        "app": "Launch applications",
        "web": "Open websites",
        "sys": "System commands",
        "file": "File operations"
    }
    
    def __init__(self):
        self.commands = {
            "app": self._handle_app_command,
            "web": self._handle_web_command,
            "sys": self._handle_sys_command,
            "file": self._handle_file_command
        }

    def execute(self, command: str) -> str:
        """Execute a command based on its category."""
        try:
            # Format: !category action params
            parts = command.split()
            if len(parts) < 2:
                return self.get_help()
                
            category = parts[0].lower()
            action = parts[1].lower()
            params = parts[2:] if len(parts) > 2 else []
            
            if category not in self.commands:
                return f"Unknown category. Available categories: {', '.join(self.COMMAND_CATEGORIES.keys())}"
                
            return self.commands[category](action, params)
            
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def _handle_app_command(self, action: str, params: list) -> str:
        """Handle application-related commands."""
        if action == "start":
            app_name = " ".join(params)
            try:
                subprocess.Popen(app_name)
                return f"Started {app_name}"
            except:
                return f"Failed to start {app_name}"
        return "Unknown app command"

    def _handle_web_command(self, action: str, params: list) -> str:
        """Handle web-related commands."""
        if action == "open":
            url = params[0] if params else "google.com"
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            return f"Opened {url}"
        return "Unknown web command"

    def _handle_sys_command(self, action: str, params: list) -> str:
        """Handle system commands."""
        actions = {
            "shutdown": "shutdown /s /t 0",
            "restart": "shutdown /r /t 0",
            "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
        }
        
        if action in actions:
            try:
                subprocess.run(actions[action], shell=True)
                return f"Executing system {action}"
            except:
                return f"Failed to execute {action}"
        return "Unknown system command"

    def _handle_file_command(self, action: str, params: list) -> str:
        """Handle file operations."""
        if action == "open":
            file_path = " ".join(params)
            try:
                os.startfile(file_path)
                return f"Opened {file_path}"
            except:
                return f"Failed to open {file_path}"
        return "Unknown file command"

    def get_help(self) -> str:
        """Return help text with available commands."""
        help_text = "Available Commands:\n\n"
        
        examples = {
            "app": "!app start chrome",
            "web": "!web open google.com",
            "sys": "!sys shutdown",
            "file": "!file open C:/path/to/file.txt"
        }
        
        for category, desc in self.COMMAND_CATEGORIES.items():
            help_text += f"{category}: {desc}\n"
            help_text += f"Example: {examples[category]}\n\n"
            
        return help_text
