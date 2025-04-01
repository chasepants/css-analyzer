# tests/test_cli.py
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
    php_file = search_dir / "page.php"
    php_file.write_text('<div class="container">PHP</div>')
    js_file = search_dir / "script.js"
    js_file.write_text('document.querySelector(".container");')
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
            mock_parser.return_value.parse.return_value = {
                ".container": (str(css_file), "2025-03-20", 20, 1, 30, False),
                ".unused": (str(css_file), "2025-03-19", 15, 1, 30, False)
            }
            mock_walk.return_value = [(str(search_dir), (), ("index.html", "page.php", "script.js"))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.side_effect = [
                [UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>', usage_commit_date="2025-03-21")],
                [UsageData(".container", "", "YES", str(search_dir / "page.php"), 1, '<div class="container">PHP</div>', usage_commit_date="2025-03-22")],
                [UsageData(".container", "", "YES", str(search_dir / "script.js"), 1, 'document.querySelector(".container");', usage_commit_date="2025-03-23")]
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once_with(str(output_file), ANY, condensed=False)

def test_main_no_files_in_search_dir(tmp_path, mock_argv):
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
            mock_parser.return_value.parse.return_value = {
                ".container": (str(css_file), "", 0, 0, 0, False)
            }
            mock_walk.return_value = [(str(search_dir), (), ())]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = []
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_analyzer_instance.analyze_file.assert_not_called()
            mock_csv_generator.generate_csv.assert_called_once_with(str(output_file), ANY, condensed=False)

def test_main_missing_css_file(mock_argv):
    css_file = "nonexistent.css"
    search_dir = "src"
    args = ["css-analyzer", "--css", css_file, "--targets", search_dir]

    with mock_argv(args):
        with pytest.raises(ValueError, match="nonexistent.css must be a CSS file"):
            main()

def test_main_custom_output_path(tmp_path, mock_argv, setup_files):
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
            mock_parser.return_value.parse.return_value = {
                ".container": (str(css_file), "2025-03-20", 20, 1, 30, False)
            }
            mock_walk.return_value = [(str(search_dir), (), ("index.html", "page.php", "script.js"))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.side_effect = [
                [UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>', usage_commit_date="2025-03-21")],
                [UsageData(".container", "", "YES", str(search_dir / "page.php"), 1, '<div class="container">PHP</div>', usage_commit_date="2025-03-22")],
                [UsageData(".container", "", "YES", str(search_dir / "script.js"), 1, 'document.querySelector(".container");', usage_commit_date="2025-03-23")]
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once_with(str(custom_output), ANY, condensed=False)

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
            mock_parser.return_value.parse.return_value = {
                ".container": (str(css_file), "2025-03-20", 20, 1, 30, False),
                ".unused": (str(css_file), "2025-03-19", 15, 1, 30, False)
            }
            mock_walk.return_value = [(str(search_dir), (), ("index.html", "page.php", "script.js"))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.side_effect = [
                [UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>', usage_commit_date="2025-03-21")],
                [],
                []
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once_with(str(output_file), ANY, condensed=False)
            call_args = mock_csv_generator.generate_csv.call_args[0]
            usages = call_args[1]
            assert len(usages) == 2
            assert any(u.selector == ".container" and u.used == "YES" and u.defined_in == str(css_file) for u in usages)
            assert any(u.selector == ".unused" and u.used == "NO" and u.defined_in == str(css_file) for u in usages)

def test_main_updates_defined_in(tmp_path, mock_argv, setup_files):
    css_file, search_dir = setup_files
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(output_file)]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.return_value = {
                ".container": (str(css_file), "2025-03-20", 20, 1, 30, False)
            }
            mock_walk.return_value = [(str(search_dir), (), ("index.html", "page.php", "script.js"))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.side_effect = [
                [UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>', usage_commit_date="2025-03-21")],
                [UsageData(".container", "", "YES", str(search_dir / "page.php"), 1, '<div class="container">PHP</div>', usage_commit_date="2025-03-22")],
                [UsageData(".container", "", "YES", str(search_dir / "script.js"), 1, 'document.querySelector(".container");', usage_commit_date="2025-03-23")]
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once_with(str(output_file), ANY, condensed=False)

def test_main_all_flag(tmp_path, mock_argv):
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
                {".container": (str(css1), "2025-03-20", 20, 1, 30, False)},
                {".header": (str(css2), "2025-03-19", 15, 1, 30, False)}
            ]
            mock_walk.return_value = [(str(search_dir), (), ("index.html",))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = [
                UsageData(".container", "", "YES", str(html_file), 1, '<div class="container">', usage_commit_date="2025-03-21")
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once_with(str(output_file), ANY, condensed=False)

def test_main_condensed_mode(tmp_path, mock_argv, setup_files):
    css_file, search_dir = setup_files
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(output_file), "-c"]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.return_value = {
                ".container": (str(css_file), "2025-03-20", 20, 1, 30, False),
                ".unused": (str(css_file), "2025-03-19", 15, 1, 30, False)
            }
            mock_walk.return_value = [(str(search_dir), (), ("index.html", "page.php", "script.js"))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.side_effect = [
                [UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>', usage_commit_date="2025-03-21")],
                [UsageData(".container", "", "YES", str(search_dir / "page.php"), 1, '<div class="container">PHP</div>', usage_commit_date="2025-03-22")],
                [UsageData(".container", "", "YES", str(search_dir / "script.js"), 1, 'document.querySelector(".container");', usage_commit_date="2025-03-23")]
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once_with(str(output_file), ANY, condensed=True)

def test_main_unused_mode(tmp_path, mock_argv, setup_files):
    css_file, search_dir = setup_files
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(output_file), "-u"]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.return_value = {
                ".container": (str(css_file), "2025-03-20", 20, 1, 30, False),
                ".unused": (str(css_file), "2025-03-19", 15, 1, 30, False)
            }
            mock_walk.return_value = [(str(search_dir), (), ("index.html", "page.php", "script.js"))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.side_effect = [
                [UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>', usage_commit_date="2025-03-21")],
                [],
                []
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_csv_generator.generate_csv.assert_called_once_with(str(output_file), ANY, condensed=False)
            call_args = mock_csv_generator.generate_csv.call_args[0]
            usages = call_args[1]
            assert len(usages) == 1
            assert all(u.used == "NO" for u in usages)

def test_main_file_type_filter(tmp_path, mock_argv, setup_files):
    css_file, search_dir = setup_files
    output_file = tmp_path / "output.csv"
    args = ["css-analyzer", "--css", str(css_file), "--targets", str(search_dir), "-o", str(output_file), "--html", "--php"]

    with mock_argv(args):
        with patch("css_analyzer.cli.CSSSelectorParser") as mock_parser, \
             patch("css_analyzer.cli.UsageDetector") as mock_detector, \
             patch("css_analyzer.cli.CSSAnalyzer") as mock_analyzer, \
             patch("css_analyzer.cli.CSVGenerator") as mock_csv_generator, \
             patch("css_analyzer.cli.os.walk") as mock_walk:
            mock_parser.return_value.parse.return_value = {
                ".container": (str(css_file), "2025-03-20", 20, 1, 30, False)
            }
            mock_walk.return_value = [(str(search_dir), (), ("index.html", "page.php", "script.js"))]
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.side_effect = [
                [UsageData(".container", "", "YES", str(search_dir / "index.html"), 1, '<div class="container">Content</div>', usage_commit_date="2025-03-21")],
                [UsageData(".container", "", "YES", str(search_dir / "page.php"), 1, '<div class="container">PHP</div>', usage_commit_date="2025-03-22")],
                []  # No JS files analyzed
            ]
            mock_csv_generator.generate_csv = Mock()

            main()

            mock_analyzer_instance.analyze_file.assert_any_call({".container"}, search_dir / "index.html")
            mock_analyzer_instance.analyze_file.assert_any_call({".container"}, search_dir / "page.php")
            assert not any(call[0][1] == search_dir / "script.js" for call in mock_analyzer_instance.analyze_file.call_args_list)
            mock_csv_generator.generate_csv.assert_called_once_with(str(output_file), ANY, condensed=False)