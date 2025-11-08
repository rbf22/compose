# compose/plugins/__init__.py
# Package initializer for plugins. Ensure submodules import so that
# side-effect registrations happen during package import.

# Import mind map plugin to trigger its auto-registration on import
from . import mindmap_plugin  # noqa: F401

# Expose plugin_manager for test compatibility
try:
    from compose.plugin_system import plugin_manager as _pm
    import builtins as _builtins
    _builtins.plugin_manager = _pm
except Exception:
    # Safe fallback if plugin_system is unavailable at import time
    pass
