# tests/test_css_selector_parser.py
import pytest
from pathlib import Path
from css_analyzer.css_selector_parser import CSSSelectorParser

@pytest.fixture
def parser():
    """Fixture to provide a fresh CSSSelectorParser instance."""
    return CSSSelectorParser()

def test_parse_basic_selectors(tmp_path, parser):
    """Test parsing basic CSS selectors."""
    css_file = tmp_path / "styles.css"
    css_file.write_text("""
        .container { width: 100%; }
        #header { color: blue; }
        div { margin: 10px; }
    """)
    result = parser.parse(css_file)
    expected = {
        ".container": str(css_file),
        "#header": str(css_file),
        "div": str(css_file)
    }
    assert result == expected

def test_parse_multiple_selectors(tmp_path, parser):
    """Test parsing multiple selectors in a single rule."""
    css_file = tmp_path / "styles.css"
    css_file.write_text("""
        .btn, .btn-primary, #submit { padding: 5px; }
    """)
    result = parser.parse(css_file)
    expected = {
        ".btn": str(css_file),
        ".btn-primary": str(css_file),
        "#submit": str(css_file)
    }
    assert result == expected

def test_parse_with_comments(tmp_path, parser):
    """Test parsing CSS with comments, ensuring they are ignored."""
    css_file = tmp_path / "styles.css"
    css_file.write_text("""
        /* This is a comment */
        .container { width: 100%; }
        /* Multi-line
           comment */
        #header { color: blue; }
    """)
    result = parser.parse(css_file)
    expected = {
        ".container": str(css_file),
        "#header": str(css_file)
    }
    assert result == expected

def test_parse_complex_selectors(tmp_path, parser):
    """Test parsing complex selectors like combinators and pseudo-classes."""
    css_file = tmp_path / "styles.css"
    css_file.write_text("""
        .container .item { margin: 5px; }
        div:hover { background: red; }
        [data-type="button"] { border: 1px solid; }
    """)
    result = parser.parse(css_file)
    expected = {
        ".container .item": str(css_file),
        "div:hover": str(css_file),
        '[data-type="button"]': str(css_file)
    }
    assert result == expected

def test_parse_empty_file(tmp_path, parser):
    """Test parsing an empty CSS file."""
    css_file = tmp_path / "styles.css"
    css_file.write_text("")
    result = parser.parse(css_file)
    assert result == {}

def test_parse_file_with_no_selectors(tmp_path, parser):
    """Test parsing a CSS file with no valid selectors."""
    css_file = tmp_path / "styles.css"
    css_file.write_text("/* Comment only */\n/* Another comment */")
    result = parser.parse(css_file)
    assert result == {}

def test_parse_nonexistent_file(tmp_path, parser):
    """Test parsing a non-existent CSS file raises an exception."""
    css_file = tmp_path / "nonexistent.css"
    with pytest.raises(FileNotFoundError):
        parser.parse(css_file)
