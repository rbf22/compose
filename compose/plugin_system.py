# compose/plugin_system.py
"""
Plugin system for Compose - extensible architecture for custom components.
Allows users to add custom renderers, parsers, processors, and transformers.
"""

import importlib
import inspect
from typing import Dict, List, Any, Optional, Callable, Type
from abc import ABC, abstractmethod
from pathlib import Path
import sys


class PluginBase(ABC):
    """Base class for all Compose plugins"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration"""
        pass

    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass


class RendererPlugin(PluginBase):
    """Plugin for custom renderers"""

    @abstractmethod
    def can_render(self, block_type: str) -> bool:
        """Check if plugin can render this block type"""
        pass

    @abstractmethod
    def render_block(self, block, config: Dict[str, Any]) -> str:
        """Render a block element"""
        pass


class ParserPlugin(PluginBase):
    """Plugin for custom parsers"""

    @abstractmethod
    def can_parse(self, content_type: str) -> bool:
        """Check if plugin can parse this content type"""
        pass

    @abstractmethod
    def parse_content(self, content: str, config: Dict[str, Any]) -> Any:
        """Parse content into AST"""
        pass


class ProcessorPlugin(PluginBase):
    """Plugin for document processors"""

    @abstractmethod
    def can_process(self, document_type: str) -> bool:
        """Check if plugin can process this document type"""
        pass

    @abstractmethod
    def process_document(self, document, config: Dict[str, Any]) -> Any:
        """Process document"""
        pass


class TransformerPlugin(PluginBase):
    """Plugin for content transformers"""

    @abstractmethod
    def can_transform(self, content_type: str) -> bool:
        """Check if plugin can transform this content type"""
        pass

    @abstractmethod
    def transform_content(self, content: str, config: Dict[str, Any]) -> str:
        """Transform content"""
        pass


class ContentPlugin(PluginBase):
    """
    Plugin for custom content types that produce UniversalBoxes.

    This allows developers to add new diagram types, custom content formats,
    and specialized content handlers that integrate seamlessly with Compose's
    layout and rendering pipeline.
    """

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Unique identifier for this content type (e.g., 'mindmap', 'circuit')"""
        pass

    def can_handle(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if this plugin can handle the given content.

        Args:
            content: The content string to check
            metadata: Optional metadata about the content

        Returns:
            True if this plugin can handle the content
        """
        return False

    @abstractmethod
    def parse_to_box(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> 'UniversalBox':
        """
        Parse content into a UniversalBox.

        Args:
            content: The content string to parse
            metadata: Optional metadata about the content

        Returns:
            UniversalBox representing the parsed content
        """
        pass

    def enhance_box(self, box: 'UniversalBox') -> 'UniversalBox':
        """
        Optionally enhance or modify the UniversalBox after parsing.

        Args:
            box: The parsed UniversalBox

        Returns:
            Enhanced UniversalBox (default: returns unchanged)
        """
        return box

    def get_dependencies(self) -> List[str]:
        """
        Return list of dependencies required by this plugin.

        Returns:
            List of package names or requirements
        """
        return []


class PluginManager:
    """
    Manages plugin loading, registration, and lifecycle.
    Provides plugin discovery and integration with the main engine.
    """

    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_dirs: List[Path] = []
        self.loaded_plugins: Dict[str, bool] = {}
        self._content_type_map: Dict[str, ContentPlugin] = {}

    def register_plugin(self, plugin_class: Type[PluginBase]) -> None:
        """
        Register a plugin class.

        Args:
            plugin_class: The plugin class to register
        """
        try:
            plugin_instance = plugin_class()
            plugin_name = plugin_instance.name

            if plugin_name in self.plugins:
                raise ValueError(f"Plugin '{plugin_name}' already registered")

            self.plugins[plugin_name] = plugin_instance

            # Handle ContentPlugins specially
            if isinstance(plugin_instance, ContentPlugin):
                content_type = plugin_instance.content_type
                if content_type in self._content_type_map:
                    raise ValueError(f"Content type '{content_type}' already registered")
                self._content_type_map[content_type] = plugin_instance

            print(f"✅ Registered plugin: {plugin_name} ({plugin_instance.__class__.__name__})")

        except Exception as e:
            print(f"❌ Failed to register plugin {plugin_class.__name__}: {e}")

    def get_content_plugin_for_type(self, content_type: str) -> Optional[ContentPlugin]:
        """Get the content plugin that handles a specific content type"""
        return self._content_type_map.get(content_type)

    def find_content_plugin_for_content(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[ContentPlugin]:
        """Find a content plugin that can handle the given content"""
        for plugin in self._content_type_map.values():
            if plugin.can_handle(content, metadata):
                return plugin
        return None

    def add_plugin_directory(self, path: str) -> None:
        """Add directory to search for plugins"""
        plugin_dir = Path(path)
        if plugin_dir.exists() and plugin_dir.is_dir():
            self.plugin_dirs.append(plugin_dir)

    def discover_plugins(self) -> List[str]:
        """Discover available plugins in plugin directories"""
        discovered = []

        for plugin_dir in self.plugin_dirs:
            # Look for Python files that might contain plugins
            for py_file in plugin_dir.glob("*.py"):
                if py_file.name.startswith("plugin_"):
                    discovered.append(py_file.stem)

        return discovered

    def load_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """
        Load a plugin by name.

        Args:
            plugin_name: Name of the plugin (without 'plugin_' prefix)
            config: Configuration for the plugin

        Returns:
            True if loaded successfully, False otherwise
        """
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]

        config = config or {}

        # Try to import the plugin module
        for plugin_dir in self.plugin_dirs:
            try:
                # Add plugin directory to Python path temporarily
                sys.path.insert(0, str(plugin_dir))

                module_name = f"plugin_{plugin_name}"
                module = importlib.import_module(module_name)

                # Look for plugin classes in the module
                plugin_class = None
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, PluginBase) and
                        obj != PluginBase):
                        plugin_class = obj
                        break

                if plugin_class:
                    # Check if it's a ContentPlugin
                    if issubclass(plugin_class, ContentPlugin):
                        # ContentPlugins are registered differently - they register themselves
                        # Just mark as loaded
                        self.loaded_plugins[plugin_name] = True
                        print(f"✅ Loaded content plugin: {plugin_name}")
                        return True
                    else:
                        # Regular plugins
                        plugin_instance = plugin_class()
                        plugin_instance.initialize(config)
                        self.plugins[plugin_name] = plugin_instance
                        self.loaded_plugins[plugin_name] = True
                        return True

            except ImportError:
                continue
            finally:
                # Remove from path
                if str(plugin_dir) in sys.path:
                    sys.path.remove(str(plugin_dir))

        self.loaded_plugins[plugin_name] = False
        return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].cleanup()
            del self.plugins[plugin_name]
            self.loaded_plugins[plugin_name] = False
            return True
        return False

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get a loaded plugin instance"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """List all loaded plugins"""
        return list(self.plugins.keys())

    def get_renderer_plugins(self) -> List[RendererPlugin]:
        """Get all renderer plugins"""
        return [p for p in self.plugins.values() if isinstance(p, RendererPlugin)]

    def get_parser_plugins(self) -> List[ParserPlugin]:
        """Get all parser plugins"""
        return [p for p in self.plugins.values() if isinstance(p, ParserPlugin)]

    def get_processor_plugins(self) -> List[ProcessorPlugin]:
        """Get all processor plugins"""
        return [p for p in self.plugins.values() if isinstance(p, ProcessorPlugin)]

    def get_transformer_plugins(self) -> List[TransformerPlugin]:
        """Get all transformer plugins"""
        return [p for p in self.plugins.values() if isinstance(p, TransformerPlugin)]

    def get_content_plugins(self) -> List[ContentPlugin]:
        """Get all content plugins"""
        return [p for p in self.plugins.values() if isinstance(p, ContentPlugin)]

    def render_with_plugins(self, block, block_type: str, config: Dict[str, Any]) -> Optional[str]:
        """
        Try to render a block using available renderer plugins.

        Returns:
            Rendered content if a plugin handled it, None otherwise
        """
        for plugin in self.get_renderer_plugins():
            if plugin.can_render(block_type):
                return plugin.render_block(block, config)
        return None

    def parse_with_plugins(self, content: str, content_type: str, config: Dict[str, Any]) -> Optional[Any]:
        """
        Try to parse content using available parser plugins.

        Returns:
            Parsed AST if a plugin handled it, None otherwise
        """
        for plugin in self.get_parser_plugins():
            if plugin.can_parse(content_type):
                return plugin.parse_content(content, config)
        return None

    def process_with_plugins(self, document, document_type: str, config: Dict[str, Any]) -> Optional[Any]:
        """
        Try to process document using available processor plugins.

        Returns:
            Processed document if a plugin handled it, None otherwise
        """
        for plugin in self.get_processor_plugins():
            if plugin.can_process(document_type):
                return plugin.process_document(document, config)
        return None

    def transform_with_plugins(self, content: str, content_type: str, config: Dict[str, Any]) -> Optional[str]:
        """
        Try to transform content using available transformer plugins.

        Returns:
            Transformed content if a plugin handled it, None otherwise
        """
        for plugin in self.get_transformer_plugins():
            if plugin.can_transform(content_type):
                return plugin.transform_content(content, config)
        return None


# Global plugin manager instance
plugin_manager = PluginManager()


def initialize_plugin_system(config: Dict[str, Any]) -> None:
    """
    Initialize the plugin system with configuration.

    Args:
        config: Configuration dictionary containing plugin settings
    """
    plugin_config = config.get('plugins', {})

    # Add plugin directories
    plugin_dirs = plugin_config.get('directories', [])
    for plugin_dir in plugin_dirs:
        plugin_manager.add_plugin_directory(plugin_dir)

    # Load specified plugins
    plugins_to_load = plugin_config.get('enabled', [])
    for plugin_name in plugins_to_load:
        plugin_config_settings = plugin_config.get(plugin_name, {})
        plugin_manager.load_plugin(plugin_name, plugin_config_settings)


def create_plugin_template(plugin_type: str, plugin_name: str) -> str:
    """
    Create a template for a new plugin.

    Args:
        plugin_type: Type of plugin ('renderer', 'parser', 'processor', 'transformer')
        plugin_name: Name of the plugin

    Returns:
        Plugin template code as string
    """
    templates = {
        'renderer': f'''# plugin_{plugin_name}.py
"""Custom renderer plugin for {plugin_name}"""

from compose.plugin_system import RendererPlugin

class {''.join(word.capitalize() for word in plugin_name.split('_'))}Renderer(RendererPlugin):
    """Custom renderer for {plugin_name} content"""

    @property
    def name(self) -> str:
        return "{plugin_name}"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_render(self, block_type: str) -> bool:
        """Check if this plugin can render the block type"""
        return block_type == "{plugin_name}"

    def render_block(self, block, config: dict) -> str:
        """Render the block to output format"""
        # Implement your custom rendering logic here
        return f"<div class='{plugin_name}'>{{block.content}}</div>"
''',

        'parser': f'''# plugin_{plugin_name}.py
"""Custom parser plugin for {plugin_name}"""

from compose.plugin_system import ParserPlugin

class {''.join(word.capitalize() for word in plugin_name.split('_'))}Parser(ParserPlugin):
    """Custom parser for {plugin_name} content"""

    @property
    def name(self) -> str:
        return "{plugin_name}"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_parse(self, content_type: str) -> bool:
        """Check if this plugin can parse the content type"""
        return content_type == "{plugin_name}"

    def parse_content(self, content: str, config: dict):
        """Parse content into AST"""
        # Implement your custom parsing logic here
        return {{"type": "{plugin_name}", "content": content}}
''',

        'processor': f'''# plugin_{plugin_name}.py
"""Custom processor plugin for {plugin_name}"""

from compose.plugin_system import ProcessorPlugin

class {''.join(word.capitalize() for word in plugin_name.split('_'))}Processor(ProcessorPlugin):
    """Custom processor for {plugin_name} documents"""

    @property
    def name(self) -> str:
        return "{plugin_name}"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_process(self, document_type: str) -> bool:
        """Check if this plugin can process the document type"""
        return document_type == "{plugin_name}"

    def process_document(self, document, config: dict):
        """Process the document"""
        # Implement your custom processing logic here
        return document
''',

        'transformer': f'''# plugin_{plugin_name}.py
"""Custom transformer plugin for {plugin_name}"""

from compose.plugin_system import TransformerPlugin

class {''.join(word.capitalize() for word in plugin_name.split('_'))}Transformer(TransformerPlugin):
    """Custom transformer for {plugin_name} content"""

    @property
    def name(self) -> str:
        return "{plugin_name}"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_transform(self, content_type: str) -> bool:
        """Check if this plugin can transform the content type"""
        return content_type == "{plugin_name}"

    def transform_content(self, content: str, config: dict) -> str:
        """Transform the content"""
        # Implement your custom transformation logic here
        return content.upper()
'''
    }

    return templates.get(plugin_type, "# Invalid plugin type")


# Example plugin implementations
class ExampleRenderer(RendererPlugin):
    """Example renderer plugin"""

    @property
    def name(self) -> str:
        return "example_renderer"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_render(self, block_type: str) -> bool:
        return block_type == "example"

    def render_block(self, block, config: Dict[str, Any]) -> str:
        return f"<div class='example'>{getattr(block, 'content', 'Example content')}</div>"


class ExampleParser(ParserPlugin):
    """Example parser plugin"""

    @property
    def name(self) -> str:
        return "example_parser"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_parse(self, content_type: str) -> bool:
        return content_type == "example"

    def parse_content(self, content: str, config: Dict[str, Any]):
        return {"type": "example", "content": content}
