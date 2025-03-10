import pytest
from unittest.mock import Mock, patch, ANY
from pathlib import Path
import sys
from contextlib import contextmanager
from css_analyzer.cli import main
from css_analyzer.types import UsageData

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
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(output_file)]

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

            mock_parser.return_value.parse.assert_called_once_with(Path(str(css_file)))
            mock_analyzer_instance.analyze_file.assert_called_once_with(
                {".container", ".unused"}, search_dir / "index.html"
            )
            mock_csv_generator.generate_csv.assert_called_once()

def test_main_no_files_in_search_dir(tmp_path, mock_argv):
    """Test main() when no files are found in the search directory."""
    css_file = tmp_path / "styles.css"
    css_file.write_text(".container { width: 100%; }")
    search_dir = tmp_path / "empty_dir"
    search_dir.mkdir()
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(output_file)]

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

            mock_analyzer_instance.analyze_file.assert_not_called()
            mock_csv_generator.generate_csv.assert_called_once()
            call_args = mock_csv_generator.generate_csv.call_args[0]
            assert len(call_args[1]) == 1
            assert call_args[1][0].selector == ".container"
            assert call_args[1][0].used == "NO"

def test_main_missing_css_file(mock_argv):
    """Test main() with a non-existent CSS file."""
    css_file = "nonexistent.css"
    search_dir = "src"
    args = ["css-analyzer", "--css", css_file, "--targets", search_dir]

    with mock_argv(args):
        with pytest.raises(ValueError, match="nonexistent.css must be a CSS file"):
            main()

def test_main_custom_output_path(tmp_path, mock_argv, setup_files):
    """Test main() with a custom output file path."""
    css_file, search_dir = setup_files
    custom_output = tmp_path / "custom" / "result.csv"
    custom_output.parent.mkdir()
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(custom_output)]

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
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(output_file)]

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
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(output_file)]

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

def test_main_all_flag(tmp_path, mock_argv):
    """Test main() with --all flag scanning a folder of CSS files."""
    css_dir = tmp_path / "css"
    css_dir.mkdir()
    css1 = css_dir / "styles1.css"
    css2 = css_dir / "styles2.css"
    css1.write_text(".container { width: 100%; }")
    css2.write_text(".header { color: blue; }")
    search_dir = tmp_path / "src"
    search_dir.mkdir()
    html_file = search_dir / "index.html"
    html_file.write_text('<div class="container">')
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", "--css", str(css_dir), "--targets", str(search_dir), "-o", str(output_file), "-a"]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.side_effect = [
                {".container": str(css1)},
                {".header": str(css2)}
            ]
            mock_walk.return_value = [(str(search_dir), (), ("index.html",))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = [
                UsageData(".container", "", "YES", str(html_file), 1, '<div class="container">')
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once()
            call_args = mock_csv_generator.generate_csv.call_args[0]
            usages = call_args[1]
            assert len(usages) == 2
            assert any(u.selector == ".container" and u.used == "YES" and u.defined_in == str(css1) for u in usages)
            assert any(u.selector == ".header" and u.used == "NO" and u.defined_in == str(css2) for u in usages)