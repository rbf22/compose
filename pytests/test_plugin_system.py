# tests/test_plugin_system.py
"""Tests for plugin system"""

import pytest
import tempfile
import os
from pathlib import Path
from compose.plugin_system import (
    PluginManager, PluginBase, RendererPlugin, ParserPlugin,
    ProcessorPlugin, TransformerPlugin, ContentPlugin, create_plugin_template,
    ExampleRenderer, ExampleParser
)
from compose.layout.universal_box import UniversalBox, ContentType


class TestPluginManager:
    """Test plugin manager functionality"""

    def test_plugin_manager_initialization(self):
        """Test creating plugin manager"""
        manager = PluginManager()
        assert len(manager.plugins) == 0
        assert len(manager.plugin_dirs) == 0
        assert len(manager.loaded_plugins) == 0

    def test_add_plugin_directory(self):
        """Test adding plugin directories"""
        manager = PluginManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            manager.add_plugin_directory(temp_dir)
            assert len(manager.plugin_dirs) == 1
            assert manager.plugin_dirs[0] == Path(temp_dir)

    def test_add_nonexistent_directory(self):
        """Test adding nonexistent directory"""
        manager = PluginManager()

        # Should not crash with nonexistent directory
        manager.add_plugin_directory("/nonexistent/path")
        assert len(manager.plugin_dirs) == 0

    def test_load_example_plugins(self):
        """Test loading built-in example plugins"""
        manager = PluginManager()

        # Create a temporary plugin file
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_file = Path(temp_dir) / "plugin_example.py"
            plugin_file.write_text("""
from compose.plugin_system import RendererPlugin

class ExampleRenderer(RendererPlugin):
    @property
    def name(self) -> str:
        return "example"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_render(self, block_type: str) -> bool:
        return block_type == "example"

    def render_block(self, block, config: dict) -> str:
        return f"<div>Rendered: {block}</div>"
""")

            manager.add_plugin_directory(temp_dir)

            # Try to load the plugin
            success = manager.load_plugin("example")
            assert success == True

            # Check if plugin is loaded
            plugin = manager.get_plugin("example")
            assert plugin is not None
            assert plugin.name == "example"
            assert plugin.version == "1.0.0"

    def test_unload_plugin(self):
        """Test unloading plugins"""
        manager = PluginManager()

        # Test unloading non-existent plugin
        success = manager.unload_plugin("nonexistent")
        assert success == False

    def test_list_plugins(self):
        """Test listing loaded plugins"""
        manager = PluginManager()

        # Initially empty
        assert manager.list_plugins() == []

        # Load a plugin
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_file = Path(temp_dir) / "plugin_list_test.py"
            plugin_file.write_text("""
from compose.plugin_system import RendererPlugin

class ListTestRenderer(RendererPlugin):
    @property
    def name(self) -> str:
        return "list_test"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_render(self, block_type: str) -> bool:
        return True

    def render_block(self, block, config: dict) -> str:
        return "test"
""")

            manager.add_plugin_directory(temp_dir)
            manager.load_plugin("list_test")

            plugins = manager.list_plugins()
            assert "list_test" in plugins

    def test_get_renderer_plugins(self):
        """Test getting renderer plugins"""
        manager = PluginManager()

        # Initially empty
        renderers = manager.get_renderer_plugins()
        assert len(renderers) == 0

        # Test that abstract classes can't be instantiated
        from compose.plugin_system import RendererPlugin
        with pytest.raises(TypeError):
            RendererPlugin()

    def test_render_with_plugins(self):
        """Test rendering with plugins"""
        manager = PluginManager()

        # Test with no plugins loaded
        result = manager.render_with_plugins("test content", "custom", {})
        assert result is None

        # Test with unsupported type
        result = manager.render_with_plugins("test content", "unsupported", {})
        assert result is None

    def test_plugin_template_creation(self):
        """Test creating plugin templates"""
        # Test renderer template
        template = create_plugin_template("renderer", "my_renderer")
        assert "class MyRendererRenderer(RendererPlugin)" in template
        assert "my_renderer" in template

        # Test parser template
        template = create_plugin_template("parser", "my_parser")
        assert "class MyParserParser(ParserPlugin)" in template
        assert "my_parser" in template

        # Test invalid type
        template = create_plugin_template("invalid", "test")
        assert template == "# Invalid plugin type"


class TestExamplePlugins:
    """Test built-in example plugins"""

    def test_example_renderer(self):
        """Test example renderer plugin"""
        renderer = ExampleRenderer()

        assert renderer.name == "example_renderer"
        assert renderer.version == "1.0.0"
        assert renderer.can_render("example") == True
        assert renderer.can_render("other") == False

        # Test rendering
        result = renderer.render_block("test block", {})
        assert result == "<div class='example'>Example content</div>"

    def test_example_parser(self):
        """Test example parser plugin"""
        parser = ExampleParser()

        assert parser.name == "example_parser"
        assert parser.version == "1.0.0"
        assert parser.can_parse("example") == True
        assert parser.can_parse("other") == False

        # Test parsing
        result = parser.parse_content("test content", {})
        assert result == {"type": "example", "content": "test content"}


class TestPluginBase:
    """Test plugin base class"""

    def test_plugin_base_is_abstract(self):
        """Test that PluginBase cannot be instantiated directly"""
        with pytest.raises(TypeError):
            PluginBase()

    def test_plugin_base_methods(self):
        """Test PluginBase default methods"""
        # Create a minimal concrete implementation
        class TestPlugin(PluginBase):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0.0"

        plugin = TestPlugin()

        # Test default methods
        plugin.initialize({})  # Should not crash
        plugin.cleanup()  # Should not crash

        assert plugin.name == "test"
        assert plugin.version == "1.0.0"


class TestContentPlugin(ContentPlugin):
    """Test content plugin implementation"""

    @property
    def name(self) -> str:
        return "test_content"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def content_type(self) -> str:
        return "test"

    def can_handle(self, content: str, metadata=None):
        return content.startswith("test:")

    def parse_to_box(self, content: str, metadata=None):
        return UniversalBox(
            content=content[5:],  # Remove "test:" prefix
            content_type=ContentType.TEXT,
            attributes={"plugin": "test"}
        )


class TestContentPlugins:
    """Test ContentPlugin functionality"""

    def test_content_plugin_registration(self):
        """Test registering a content plugin"""
        manager = PluginManager()

        # Register test plugin
        manager.register_plugin(TestContentPlugin)

        # Check registration
        plugins = manager.get_content_plugins()
        assert len(plugins) == 1
        assert plugins[0].content_type == "test"

        # Check content type lookup
        plugin = manager.get_content_plugin_for_type("test")
        assert plugin is not None
        assert plugin.content_type == "test"

    def test_content_plugin_parsing(self):
        """Test content plugin parsing functionality"""
        manager = PluginManager()
        manager.register_plugin(TestContentPlugin)

        # Test parsing
        plugin = manager.get_content_plugin_for_type("test")
        assert plugin is not None

        box = plugin.parse_to_box("test:hello world")
        assert isinstance(box, UniversalBox)
        assert box.content == "hello world"
        assert box.attributes.get("plugin") == "test"

    def test_plugin_content_detection(self):
        """Test finding plugins for content"""
        manager = PluginManager()
        manager.register_plugin(TestContentPlugin)

        # Test detection
        plugin = manager.find_content_plugin_for_content("test:some content")
        assert plugin is not None
        assert plugin.content_type == "test"

        # Test non-matching content
        plugin = manager.find_content_plugin_for_content("regular content")
        assert plugin is None

    def test_mindmap_plugin_registration(self):
        """Test that the mind map plugin is auto-registered"""
        # The mind map plugin should auto-register when imported
        from compose.plugins import mindmap_plugin

        # Check that it's registered
        plugin = plugin_manager.get_content_plugin_for_type("mindmap")
        assert plugin is not None
        assert plugin.content_type == "mindmap"

    def test_mindmap_plugin_parsing(self):
        """Test mind map plugin parsing"""
        from compose.plugins import mindmap_plugin

        plugin = plugin_manager.get_content_plugin_for_type("mindmap")
        assert plugin is not None

        # Test basic mind map parsing
        mindmap_content = """mindmap
Central Idea
  Branch 1
    Sub-branch 1.1
  Branch 2"""

        box = plugin.parse_to_box(mindmap_content)
        assert isinstance(box, UniversalBox)
        assert box.content_type == ContentType.DIAGRAM
        assert 'nodes' in box.content
        assert len(box.content['nodes']) > 0

    def test_content_plugin_enhancement(self):
        """Test content plugin box enhancement"""
        manager = PluginManager()
        manager.register_plugin(TestContentPlugin)

        plugin = manager.get_content_plugin_for_type("test")
        assert plugin is not None

        # Create a basic box
        box = UniversalBox(content="test", content_type=ContentType.TEXT)

        # Enhance it
        enhanced = plugin.enhance_box(box)
        assert enhanced is box  # Default implementation returns unchanged

    def test_plugin_dependencies(self):
        """Test plugin dependency reporting"""
        plugin = TestContentPlugin()
        deps = plugin.get_dependencies()
        assert isinstance(deps, list)

        # Test content plugin has no dependencies by default
        assert len(deps) == 0
