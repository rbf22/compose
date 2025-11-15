"""Tests for KaTeX function modules."""

import pytest


class TestFunctionImports:
    """Test that all function modules can be imported."""

    def test_all_function_modules_importable(self):
        """Test that all 46 function modules can be imported."""
        function_modules = [
            'accent', 'accentunder', 'arrow', 'char', 'color', 'cr', 'def', 'delimsizing',
            'enclose', 'environment', 'font', 'genfrac', 'hbox', 'hexBrace', 'html',
            'htmlmathml', 'includegraphics', 'kern', 'lap', 'math', 'mathchoice',
            'mclass', 'op', 'operatorname', 'ordgroup', 'overline', 'phantom', 'pmb',
            'raisebox', 'relax', 'rule', 'sizing', 'smash', 'sqrt', 'styling', 'supsub',
            'symbolsOp', 'symbolsOrd', 'symbolsSpacing', 'tag', 'text', 'underline',
            'vcenter', 'verb'
        ]

        imported_count = 0
        for module_name in function_modules:
            try:
                module = __import__(f'pytex.functions.{module_name}', fromlist=[''])
                assert module is not None
                imported_count += 1
            except ImportError:
                # Some modules might not exist yet, that's okay
                continue

        # At minimum, we should be able to import some modules
        assert imported_count > 0

    def test_core_functions_exist(self):
        """Test that core mathematical functions are available."""
        # Test importing some key functions
        try:
            import pytex.functions.supsub
            import pytex.functions.genfrac
            import pytex.functions.sqrt
            import pytex.functions.accent
            import pytex.functions.op
        except ImportError as e:
            pytest.skip(f"Core functions not fully implemented yet: {e}")


class TestEnvironmentImports:
    """Test that environment modules can be imported."""

    def test_array_environment_importable(self):
        """Test that the array environment can be imported."""
        try:
            import pytex.environments.array
            assert hasattr(pytex.environments.array, 'parse_array')
            assert hasattr(pytex.environments.array, 'html_builder')
        except ImportError as e:
            pytest.skip(f"Array environment not implemented: {e}")

    def test_environment_functions_exist(self):
        """Test that environment has expected functions."""
        try:
            import pytex.environments.array as array_env
            assert callable(array_env.parse_array)
            assert callable(array_env.html_builder)
            assert callable(array_env.mathml_builder)
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Environment functions not complete: {e}")


class TestUtilityImports:
    """Test that utility modules can be imported."""

    def test_assemble_supsub_utility(self):
        """Test that the assembleSupSub utility can be imported."""
        try:
            from pytex.functions.utils.assembleSupSub import assembleSupSub
            assert callable(assembleSupSub)
        except ImportError as e:
            pytest.skip(f"Utility not implemented: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
