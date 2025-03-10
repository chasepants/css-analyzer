# tests/test_cli.py
import pytest
from unittest.mock import Mock, patch, ANY  # Added ANY import
from pathlib import Path
import sys
from contextlib import contextmanager
from css_analyzer.cli import main
from css_analyzer.types import UsageData

# Fixture for mocking sys.argv as a context manager
@pytest.fixture
def mock_argv():
    @contextmanager
    def _mock_argv(args):
        original_argv = sys.argv
        sys.argv = args
        try:
            yield
        finally:
            sys.argv = original_argv
    return _mock_argv

# Fixture for temporary CSS and search directory setup
@pytest.fixture
def setup_files(tmp_path):
    css_file = tmp_path / "styles.css"
    css_file.write_text(".container { width: 100%; }\n.unused { display: none; }")
    search_dir = tmp_path / "src"
    search_dir.mkdir()
    html_file = search_dir / "index.html"
    html_file.write_text('<div class="container">Content</div>')
    return css_file, search_dir

def test_main_basic_execution(tmp_path, mock_argv, setup_files):
    """Test basic execution of main() with valid arguments."""
    css_file, search_dir = setup_files
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", str(css_file), str(search_dir), "-o", str(output_file)]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            # Mock parser
            mock_parser.return_value.parse.return_value = {".container": str(css_file), ".unused": str(css_file)}
            
            # Mock file traversal
            mock_walk.return_value = [(str(search_dir), (), ("index.html",))]
            
            # Mock analyzer
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = [
                UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>')
            ]
            
            # Mock CSV generator
            mock_csv_generator.generate_csv = Mock()

            main()

            # Verify calls
            mock_parser.return_value.parse.assert_called_once_with(Path(str(css_file)))
            mock_analyzer_instance.analyze_file.assert_called_once_with(
                {".container", ".unused"}, search_dir / "index.html"
            )
            mock_csv_generator.generate_csv.assert_called_once()
            # Removed assert output_file.exists() since CSV generation is mocked

def test_main_no_files_in_search_dir(tmp_path, mock_argv):
    """Test main() when no files are found in the search directory."""
    css_file = tmp_path / "styles.css"
    css_file.write_text(".container { width: 100%; }")
    search_dir = tmp_path / "empty_dir"
    search_dir.mkdir()
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", str(css_file), str(search_dir), "-o", str(output_file)]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.return_value = {".container": str(css_file)}
            mock_walk.return_value = [(str(search_dir), (), ())]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = []
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_analyzer_instance.analyze_file.assert_not_called()  # No files to analyze
            mock_csv_generator.generate_csv.assert_called_once()
            # Check that unused selectors are still written
            call_args = mock_csv_generator.generate_csv.call_args[0]
            assert len(call_args[1]) == 1  # Only .container as unused
            assert call_args[1][0].selector == ".container"
            assert call_args[1][0].used == "NO"

def test_main_missing_css_file(mock_argv):
    """Test main() with a non-existent CSS file."""
    css_file = "nonexistent.css"
    search_dir = "src"
    args = ["css-analyzer", css_file, search_dir]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser:
            mock_parser.return_value.parse.side_effect = FileNotFoundError
            with pytest.raises(FileNotFoundError):
                main()

def test_main_custom_output_path(tmp_path, mock_argv, setup_files):
    """Test main() with a custom output file path."""
    css_file, search_dir = setup_files
    custom_output = tmp_path / "custom" / "result.csv"
    custom_output.parent.mkdir()
    args = ["css-analyzer", str(css_file), str(search_dir), "-o", str(custom_output)]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.return_value = {".container": str(css_file)}
            mock_walk.return_value = [(str(search_dir), (), ("index.html",))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = [
                UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>')
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once_with(str(custom_output), ANY)

def test_main_finalizes_unused_selectors(tmp_path, mock_argv, setup_files):
    """Test that main() includes unused selectors in the output."""
    css_file, search_dir = setup_files
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", str(css_file), str(search_dir), "-o", str(output_file)]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.return_value = {".container": str(css_file), ".unused": str(css_file)}
            mock_walk.return_value = [(str(search_dir), (), ("index.html",))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = [
                UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>')
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            call_args = mock_csv_generator.generate_csv.call_args[0]
            usages = call_args[1]
            assert len(usages) == 2
            assert any(u.selector == ".container" and u.used == "YES" and u.defined_in == str(css_file) for u in usages)
            assert any(u.selector == ".unused" and u.used == "NO" and u.defined_in == str(css_file) for u in usages)

def test_main_updates_defined_in(tmp_path, mock_argv, setup_files):
    """Test that main() updates defined_in for used selectors."""
    css_file, search_dir = setup_files
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", str(css_file), str(search_dir), "-o", str(output_file)]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.return_value = {".container": str(css_file)}
            mock_walk.return_value = [(str(search_dir), (), ("index.html",))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = [
                UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>')
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            call_args = mock_csv_generator.generate_csv.call_args[0]
            usages = call_args[1]
            assert len(usages) == 1
            assert usages[0].defined_in == str(css_file)