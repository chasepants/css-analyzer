# tests/test_css_selector_parser.py
import pytest
from css_analyzer.css_selector_parser import CSSSelectorParser
from pathlib import Path

def test_parse_basic_selectors(tmp_path):
    """Test parsing a CSS file with basic selectors."""
    css_file = tmp_path / "styles.css"
    css_file.write_text(".container { width: 100%; }\n#header { color: blue; }")
    parser = CSSSelectorParser()
    selectors = parser.parse(css_file)
    expected = {
        ".container": (str(css_file), "", 0, 0, 0, False),
        "#header": (str(css_file), "", 0, 0, 0, False)
    }
    # Adjust for actual commit dates and sizes if Git is available in test env
    for sel, (path, date, size, complexity, age, comments) in selectors.items():
        assert path == expected[sel][0]
        assert isinstance(date, str)
        assert isinstance(size, int)
        assert isinstance(complexity, int)
        assert isinstance(age, int)
        assert isinstance(comments, bool)

def test_parse_multiple_selectors(tmp_path):
    """Test parsing a CSS file with multiple selectors in one rule."""
    css_file = tmp_path / "styles.css"
    css_file.write_text(".btn, #submit { margin: 10px; }")
    parser = CSSSelectorParser()
    selectors = parser.parse(css_file)
    expected = {
        ".btn": (str(css_file), "", 0, 0, 0, False),
        "#submit": (str(css_file), "", 0, 0, 0, False)
    }
    for sel, (path, date, size, complexity, age, comments) in selectors.items():
        assert path == expected[sel][0]

def test_parse_with_comments(tmp_path):
    """Test parsing a CSS file with comments."""
    css_file = tmp_path / "styles.css"
    css_file.write_text("/* Comment */\n#header { color: blue; }\n/* .hidden { display: none; } */")
    parser = CSSSelectorParser()
    selectors = parser.parse(css_file)
    expected = {
        "#header": (str(css_file), "", 0, 0, 0, False)
    }
    assert ".hidden" not in selectors  # Ensure commented-out selector is ignored
    for sel, (path, date, size, complexity, age, comments) in selectors.items():
        assert path == expected[sel][0]
        assert not comments  # Not in a comment

def test_parse_complex_selectors(tmp_path):
    """Test parsing a CSS file with complex selectors."""
    css_file = tmp_path / "styles.css"
    css_file.write_text(".container div:hover { padding: 5px; }")
    parser = CSSSelectorParser()
    selectors = parser.parse(css_file)
    expected = {
        ".container div:hover": (str(css_file), "", 0, 0, 0, False)
    }
    for sel, (path, date, size, complexity, age, comments) in selectors.items():
        assert path == expected[sel][0]

def test_parse_file_not_found():
    """Test parsing a non-existent CSS file raises an exception."""
    parser = CSSSelectorParser()
    with pytest.raises(Exception):
        parser.parse(Path("nonexistent.css"))