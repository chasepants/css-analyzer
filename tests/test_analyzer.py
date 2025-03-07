# tests/test_analyzer.py
import pytest
from pathlib import Path
from css_analyzer.analyzer import CSSSelectorParser, UsageDetector, CSSAnalyzer
import csv
import io

@pytest.fixture
def css_content():
    """Sample CSS content for testing."""
    return """
    /* styles.css */
    .container { width: 80%; }
    #main { padding: 20px; }
    div { border: 1px solid #ccc; }
    p.error { color: red; }
    [data-type="button"] { cursor: pointer; }
    .btn:hover { background: blue; }
    .unused { display: none; }
    """

@pytest.fixture
def html_content():
    """Sample HTML content for testing."""
    return """
    <div class="container">
        <p id="main">Text</p>
        <p class="error">Error</p>
        <button data-type="button">Click</button>
    </div>
    """

@pytest.fixture
def php_content():
    """Sample PHP content for testing."""
    return """
    <?php
    echo '<div class="container">';
    echo '<button id="main" data-type="button">Click</button>';
    ?>
    """

def test_css_selector_parser(tmp_path):
    """Test CSSSelectorParser parsing selectors."""
    css_file = tmp_path / "test.css"
    with open(css_file, 'w') as f:
        f.write("""
        .container { width: 80%; }
        #main { padding: 20px; }
        div { border: 1px solid #ccc; }
        p.error { color: red; }
        [data-type="button"] { cursor: pointer; }
        """)
    
    parser = CSSSelectorParser()
    selectors = parser.parse(css_file)
    
    assert ".container" in selectors
    assert "#main" in selectors
    assert "div" in selectors
    assert "p.error" in selectors
    assert '[data-type="button"]' in selectors
    assert len(selectors) == 5

def test_usage_detector_classes():
    """Test UsageDetector class detection."""
    detector = UsageDetector()
    line = '<div class="container btn">'
    selectors = {".container", ".btn", ".other"}
    usages = detector.detect_class_usage(line, selectors)
    
    assert len(usages) == 2
    assert usages[0] == (".container", line)
    assert usages[1] == (".btn", line)

def test_usage_detector_ids():
    """Test UsageDetector ID detection."""
    detector = UsageDetector()
    line = '<p id="main">'
    selectors = {"#main", "#other"}
    usages = detector.detect_id_usage(line, selectors)
    
    assert len(usages) == 1
    assert usages[0] == ("#main", line)

def test_usage_detector_elements():
    """Test UsageDetector element detection."""
    detector = UsageDetector()
    line = '<div class="container">'
    selectors = {"div", "p"}
    usages = detector.detect_element_usage(line, selectors)
    
    assert len(usages) == 1
    assert usages[0] == ("div", line)

def test_usage_detector_attributes():
    """Test UsageDetector attribute detection."""
    detector = UsageDetector()
    line = '<button data-type="button" class="btn">'
    selectors = {'[data-type="button"]', '[type="text"]'}
    usages = detector.detect_attribute_usage(line, selectors)
    
    assert len(usages) == 1
    assert usages[0] == ('[data-type="button"]', line)

def test_usage_detector_combo():
    """Test UsageDetector combo selector detection."""
    detector = UsageDetector()
    line = '<p class="error">'
    selectors = {"p.error", "div.container"}
    usages = detector.detect_combo_usage(line, selectors)
    
    assert len(usages) == 1
    assert usages[0] == ("p.error", line)

def test_usage_detector_echo():
    """Test UsageDetector echo detection."""
    detector = UsageDetector()
    line = 'echo \'<div class="container" id="main">\';'
    selectors = {".container", "#main", "div"}
    usages = detector.detect_echo_usage(line, selectors)
    
    assert len(usages) == 3
    assert (".container", line) in usages
    assert ("#main", line) in usages
    assert ("div", line) in usages

def test_css_analyzer(tmp_path, css_content, html_content, php_content):
    """Test CSSAnalyzer end-to-end."""
    # Setup test files
    css_file = tmp_path / "styles.css"
    html_file = tmp_path / "test.html"
    php_file = tmp_path / "test.php"
    output_csv = tmp_path / "output.csv"

    css_file.write_text(css_content)
    html_file.write_text(html_content)
    php_file.write_text(php_content)

    # Run analyzer
    analyzer = CSSAnalyzer(str(css_file), tmp_path)
    analyzer.parse_css()
    analyzer.find_usages()
    analyzer.generate_csv(str(output_csv))

    # Read and verify CSV
    with open(output_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 7  # At least one row per selector
    used_selectors = {row['CSS Element'] for row in rows if row['Used?'] == 'YES'}
    assert ".container" in used_selectors
    assert "#main" in used_selectors
    assert "div" in used_selectors
    assert "p.error" in used_selectors
    assert '[data-type="button"]' in used_selectors
    assert any(row['CSS Element'] == ".unused" and row['Used?'] == 'NO' for row in rows)
    assert any(row['CSS Element'] == ".btn:hover" and row['Used?'] == 'UNKNOWN' for row in rows)

def test_combinator_detection(tmp_path):
    """Test combinator detection across multiple lines."""
    html_file = tmp_path / "test.html"
    html_file.write_text(
        '<div class="container">\n'
        '    <header class="header">\n'
    )
    css_file = tmp_path / "test.css"
    css_file.write_text('.container .header { color: blue; }\n')

    analyzer = CSSAnalyzer(str(css_file), tmp_path)
    analyzer.parse_css()
    analyzer.find_usages()
    
    assert any(selector == '.container .header' for selector, _, _, _ in analyzer.usages)