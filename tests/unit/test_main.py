"""
Unit tests for episia.__main__ module
Tests for CLI documentation display and color formatting
"""
import pytest
import sys
from unittest import mock
from io import StringIO

# Import functions to test
from episia.__main__ import (
    _rgb, _bold, _dim, _supports_color, _lerp_color,
    _render_logo, _get_version, _get_python_version,
    _section, _print_doc, main, _LOGO, _GRADIENT, _MODULES
)



# ANSI COLOR FORMATTING TESTS

class TestRGBFormatting:
    """Test ANSI RGB color formatting"""
    
    def test_rgb_basic(self):
        """Should format RGB color in ANSI escape sequence"""
        result = _rgb(255, 0, 0, "text")
        assert "38;2;255;0;0m" in result
        assert "text" in result
        assert "\033[" in result
        assert "\033[0m" in result
    
    def test_rgb_preserves_text(self):
        """Should preserve the original text"""
        text = "Hello World"
        result = _rgb(100, 150, 200, text)
        assert text in result
    
    def test_rgb_with_different_colors(self):
        """Should work with different RGB values"""
        r1 = _rgb(0, 0, 0, "black")
        r2 = _rgb(255, 255, 255, "white")
        assert r1 != r2
        assert "0;0;0m" in r1
        assert "255;255;255m" in r2
    
    def test_rgb_with_empty_text(self):
        """Should handle empty text"""
        result = _rgb(100, 100, 100, "")
        assert "\033[38;2;100;100;100m\033[0m" in result


class TestBoldFormatting:
    """Test ANSI bold formatting"""
    
    def test_bold_basic(self):
        """Should add bold ANSI escape sequence"""
        result = _bold("text")
        assert "\033[1m" in result
        assert "text" in result
        assert "\033[0m" in result
    
    def test_bold_preserves_text(self):
        """Should preserve the original text"""
        text = "Bold Text"
        result = _bold(text)
        assert text in result
    
    def test_bold_empty_string(self):
        """Should handle empty string"""
        result = _bold("")
        assert "\033[1m\033[0m" in result


class TestDimFormatting:
    """Test ANSI dim formatting"""
    
    def test_dim_basic(self):
        """Should add dim ANSI escape sequence"""
        result = _dim("text")
        assert "\033[2m" in result
        assert "text" in result
        assert "\033[0m" in result
    
    def test_dim_preserves_text(self):
        """Should preserve the original text"""
        text = "Dim Text"
        result = _dim(text)
        assert text in result
    
    def test_dim_empty_string(self):
        """Should handle empty string"""
        result = _dim("")
        assert "\033[2m\033[0m" in result



# COLOR SUPPORT DETECTION TESTS

class TestColorSupport:
    """Test color support detection"""
    
    @mock.patch("sys.platform", "linux")
    @mock.patch("sys.stdout.isatty", return_value=True)
    def test_color_support_linux_tty(self, mock_isatty):
        """Should detect color support on Linux TTY"""
        result = _supports_color()
        assert result is True
    
    @mock.patch("sys.platform", "linux")
    @mock.patch("sys.stdout.isatty", return_value=False)
    def test_color_support_linux_no_tty(self, mock_isatty):
        """Should detect no color on Linux without TTY"""
        result = _supports_color()
        assert result is False
    
    @mock.patch("sys.platform", "win32")
    def test_color_support_windows(self):
        """Should handle Windows platform"""
        result = _supports_color()
        assert isinstance(result, bool)
    
    @mock.patch("sys.platform", "darwin")
    @mock.patch("sys.stdout.isatty", return_value=True)
    def test_color_support_macos_tty(self, mock_isatty):
        """Should detect color support on macOS TTY"""
        result = _supports_color()
        assert result is True



# COLOR INTERPOLATION TESTS

class TestLerpColor:
    """Test color interpolation (lerp)"""
    
    def test_lerp_at_start(self):
        """Should return first color at t=0"""
        stops = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        result = _lerp_color(stops, 0.0)
        assert result == (255, 0, 0)
    
    def test_lerp_at_end(self):
        """Should return last color at t=1"""
        stops = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        result = _lerp_color(stops, 1.0)
        assert result == (0, 0, 255)
    
    def test_lerp_at_middle(self):
        """Should interpolate at t=0.5"""
        stops = [(0, 0, 0), (100, 100, 100)]
        result = _lerp_color(stops, 0.5)
        # Should be approximately (50, 50, 50)
        assert 40 <= result[0] <= 60
        assert 40 <= result[1] <= 60
        assert 40 <= result[2] <= 60
    
    def test_lerp_with_negative_t(self):
        """Should clamp negative t to start"""
        stops = [(255, 0, 0), (0, 255, 0)]
        result = _lerp_color(stops, -0.5)
        assert result == (255, 0, 0)
    
    def test_lerp_with_large_t(self):
        """Should clamp t > 1 to end"""
        stops = [(255, 0, 0), (0, 255, 0)]
        result = _lerp_color(stops, 1.5)
        assert result == (0, 255, 0)



# VERSION DETECTION TESTS

class TestVersionDetection:
    """Test version and Python version retrieval"""
    
    def test_get_version(self):
        """Should return a version string"""
        version = _get_version()
        assert isinstance(version, str)
        assert len(version) > 0
        # Should be in format like "0.1.0" or similar
        assert any(c.isdigit() for c in version)
    
    def test_get_python_version(self):
        """Should return Python version string"""
        py_ver = _get_python_version()
        assert isinstance(py_ver, str)
        # Should contain dots and digits
        assert "." in py_ver
        assert py_ver.count(".") >= 2
        # Should match format X.Y.Z
        parts = py_ver.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)



# LOGO RENDERING TESTS

class TestLogoRendering:
    """Test logo rendering with and without colors"""
    
    def test_render_logo_without_color(self):
        """Should render logo without color codes"""
        result = _render_logo(False)
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not contain ANSI escape codes
        assert "\033[" not in result
        # Should contain logo characters
        assert "█" in result or "#" in result
    
    def test_render_logo_with_color(self):
        """Should render logo with ANSI color codes"""
        result = _render_logo(True)
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain ANSI escape codes
        assert "\033[" in result
        assert "38;2;" in result  # RGB color codes
    
    def test_render_logo_contains_all_lines(self):
        """Should render all logo lines"""
        result = _render_logo(False)
        # Count newlines (should be same as logo lines - 1)
        newline_count = result.count("\n")
        assert newline_count >= len(_LOGO) - 1
    
    def test_render_logo_consistent(self):
        """Same input should produce same output"""
        result1 = _render_logo(False)
        result2 = _render_logo(False)
        assert result1 == result2



# SECTION FORMATTING TESTS

class TestSectionFormatting:
    """Test section title formatting"""
    
    def test_section_without_color(self):
        """Should format section without color"""
        result = _section("Test Module", False, (100, 100, 100))
        assert "Test Module" in result
        assert "\033[" not in result
    
    def test_section_with_color(self):
        """Should format section with color"""
        result = _section("Test Module", True, (255, 0, 0))
        assert "Test Module" in result
        assert "\033[" in result
    
    def test_section_includes_padding(self):
        """Should include padding spaces"""
        result = _section("Title", False, (0, 0, 0))
        assert "  " in result  # Should have leading spaces



# DOCUMENTATION PRINTING TESTS

class TestDocPrinting:
    """Test documentation printing"""
    
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_print_doc_without_color(self, mock_stdout):
        """Should print documentation without color"""
        _print_doc(False)
        output = mock_stdout.getvalue()
        assert len(output) > 0
        assert "episia" in output.lower()
        # Should not have excessive ANSI codes
        assert output.count("\033[") < 10
    
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_print_doc_with_color(self, mock_stdout):
        """Should print documentation with color"""
        _print_doc(True)
        output = mock_stdout.getvalue()
        assert len(output) > 0
        assert "episia" in output.lower()
        # Should have ANSI color codes
        assert "\033[" in output
    
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_print_doc_contains_modules(self, mock_stdout):
        """Should include module information"""
        _print_doc(False)
        output = mock_stdout.getvalue()
        # Should mention at least one module
        assert any(mod[0] in output for mod in _MODULES)
    
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_print_doc_contains_quick_start(self, mock_stdout):
        """Should include quick start code"""
        _print_doc(False)
        output = mock_stdout.getvalue()
        assert "Quick start" in output or "quick start" in output.lower()
        assert "epi.seir" in output or "SEIR" in output



# MAIN FUNCTION TESTS

class TestMainFunction:
    """Test main entry point"""
    
    @mock.patch("episia.__main__._print_doc")
    @mock.patch("episia.__main__._supports_color", return_value=True)
    def test_main_calls_print_doc(self, mock_color, mock_print):
        """Main should call _print_doc with color support"""
        main()
        mock_print.assert_called_once()
        # Should be called with True for color
        mock_print.assert_called_with(True)
    
    @mock.patch("episia.__main__._print_doc")
    @mock.patch("episia.__main__._supports_color", return_value=False)
    def test_main_without_color(self, mock_color, mock_print):
        """Main should call _print_doc without color"""
        main()
        mock_print.assert_called_once()
        # Should be called with False
        mock_print.assert_called_with(False)
    
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_main_produces_output(self, mock_stdout):
        """Main should produce output"""
        main()
        output = mock_stdout.getvalue()
        assert len(output) > 0



# INTEGRATION TESTS

class TestIntegration:
    """Integration tests for full CLI"""
    
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_cli_execution(self, mock_stdout):
        """Complete CLI execution should produce valid output"""
        main()
        output = mock_stdout.getvalue()
        
        # Should contain key elements
        assert len(output) > 100  # Substantial output
        assert "episia" in output.lower()
        assert any(mod[0] in output for mod in _MODULES)  # At least one module
        # Should have some formatting
        assert "\n" in output
    
    def test_logo_is_defined(self):
        """Logo should be properly defined"""
        assert isinstance(_LOGO, list)
        assert len(_LOGO) > 0
        assert all(isinstance(line, str) for line in _LOGO)
    
    def test_gradient_is_defined(self):
        """Gradient colors should be properly defined"""
        assert isinstance(_GRADIENT, list)
        assert len(_GRADIENT) > 0
        assert all(isinstance(color, tuple) and len(color) == 3 for color in _GRADIENT)
    
    def test_modules_are_defined(self):
        """Module catalogue should be properly defined"""
        assert isinstance(_MODULES, list)
        assert len(_MODULES) > 0
        for mod in _MODULES:
            assert isinstance(mod, tuple)
            assert len(mod) == 3
            assert isinstance(mod[0], str)  # module name
            assert isinstance(mod[1], str)  # description
            assert isinstance(mod[2], list)  # functions



# EDGE CASE TESTS

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_rgb_with_zero_values(self):
        """RGB with zero values should work"""
        result = _rgb(0, 0, 0, "black")
        assert "0;0;0m" in result
    
    def test_rgb_with_max_values(self):
        """RGB with max values (255) should work"""
        result = _rgb(255, 255, 255, "white")
        assert "255;255;255m" in result
    
    def test_bold_multiple_times(self):
        """Nested bold should still work"""
        text = "text"
        result = _bold(_bold(text))
        assert text in result
    
    def test_lerp_with_single_color_stop(self):
        """Lerp with single stop should return that color"""
        stops = [(100, 100, 100)]
        result = _lerp_color(stops, 0.5)
        assert result == (100, 100, 100)
    
    def test_render_logo_is_consistent(self):
        """Logo rendering should be deterministic"""
        logo1 = _render_logo(True)
        logo2 = _render_logo(True)
        assert logo1 == logo2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])