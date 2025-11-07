# compose/plugins.py

import importlib
import os
from typing import Dict, List, Any, Optional
from .model.document import Node

class PluginManager:
    """Simple plugin manager for extending Compose functionality"""

    def __init__(self):
        self.parsers = {}  # name -> parser_function
        self.renderers = {}  # name -> renderer_function
        self.loaded_plugins = set()

    def load_plugin(self, plugin_name: str):
        """Load a plugin by name"""
        if plugin_name in self.loaded_plugins:
            return

        try:
            # Try to import as a module
            plugin_module = importlib.import_module(f'compose.plugins.{plugin_name}')

            # Register parser if available
            if hasattr(plugin_module, 'parse'):
                self.parsers[plugin_name] = plugin_module.parse

            # Register renderer if available
            if hasattr(plugin_module, 'render'):
                self.renderers[plugin_name] = plugin_module.render

            self.loaded_plugins.add(plugin_name)

        except ImportError:
            # Plugin not found, skip silently
            pass

    def get_parser(self, name: str):
        """Get a parser function by name"""
        return self.parsers.get(name)

    def get_renderer(self, name: str):
        """Get a renderer function by name"""
        return self.renderers.get(name)

    def list_plugins(self) -> Dict[str, List[str]]:
        """List available plugins"""
        return {
            'parsers': list(self.parsers.keys()),
            'renderers': list(self.renderers.keys())
        }

# Global plugin manager instance
plugin_manager = PluginManager()

def load_builtin_plugins():
    """Load built-in plugins"""
    # For now, we don't have any built-in plugins beyond the core functionality
    # This could be extended to load plugins from a plugins directory
    pass

# Example plugin structure:
"""
# compose/plugins/custom_parser.py

def parse(content: str, config: dict) -> List[Node]:
    '''Custom parser implementation'''
    # Your parsing logic here
    return []

# compose/plugins/custom_renderer.py

def render(nodes: List[Node], config: dict) -> str:
    '''Custom renderer implementation'''
    # Your rendering logic here
    return ""
"""
