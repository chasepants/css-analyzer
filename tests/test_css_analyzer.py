import pytest
from unittest.mock import Mock
from css_analyzer.css_analyzer import CSSAnalyzer
from css_analyzer.types import UsageData

# Mock UsageDetector for controlled testing
@pytest.fixture
def mock_detector():
    detector = Mock()
    # Default behavior: return empty list unless specified
    detector.detect_class_usage.return_value = []
    detector.detect_id_usage.return_value = []
    detector.detect_element_usage.return_value = []
    detector.detect_attribute_usage.return_value = []
    detector.detect_combo_usage.return_value = []
    detector.detect_echo_usage.return_value = []
    detector.detect_pseudo_usage.return_value = []
    detector.php_var_pattern = r'^\s*\$[\w]+'
    detector.html_tag_pattern = r'<[^>]+class=["\'][^>]*>'
    detector.element_pattern = r'<([a-zA-Z][\w-]*)\b[^>]*'
    return detector

@pytest.fixture
def analyzer(mock_detector):
    return CSSAnalyzer(mock_detector)

def test_init_with_detector(analyzer, mock_detector):
    """Test that CSSAnalyzer initializes with the provided detector."""
    assert analyzer.detector == mock_detector

def test_add_usage_unique(tmp_path, analyzer):
    """Test that _add_usage adds only unique entries."""
    usages = []
    seen = set()
    file_path = str(tmp_path / "test.html")

    # Add first usage
    analyzer._add_usage(usages, seen, ".container", file_path, 1, '<div class="container">')
    assert len(usages) == 1
    assert usages[0] == UsageData(
        selector=".container",
        defined_in="",
        used="YES",
        file=file_path,
        line_number=1,
        line='<div class="container">'
    )

    # Try adding duplicate
    analyzer._add_usage(usages, seen, ".container", file_path, 1, '<div class="container">')
    assert len(usages) == 1  # No duplicate added

    # Add different selector on same line
    analyzer._add_usage(usages, seen, "div", file_path, 1, '<div class="container">')
    assert len(usages) == 2  # Different selector allowed

def test_analyze_file_html_class_detection(tmp_path, analyzer, mock_detector):
    """Test HTML file analysis with class detection."""
    html_file = tmp_path / "test.html"
    html_file.write_text('<div class="container">Content</div>')
    selectors = {".container", "div"}

    mock_detector.detect_class_usage.return_value = [(".container", '<div class="container">Content</div>')]
    mock_detector.detect_element_usage.return_value = [("div", '<div class="container">Content</div>')]

    result = analyzer.analyze_file(selectors, html_file)
    assert len(result) == 2
    assert UsageData(".container", "", "YES", str(html_file), 1, '<div class="container">Content</div>') in result
    assert UsageData("div", "", "YES", str(html_file), 1, '<div class="container">Content</div>') in result

def test_analyze_file_js_pseudo_class(tmp_path, analyzer, mock_detector):
    """Test JS file analysis with pseudo-class detection."""
    js_file = tmp_path / "script.js"
    js_file.write_text('document.querySelector(".btn").classList.add("btn:hover");')
    selectors = {".btn:hover"}

    mock_detector.detect_pseudo_usage.return_value = [(".btn:hover", 'document.querySelector(".btn").classList.add("btn:hover");')]

    result = analyzer.analyze_file(selectors, js_file)
    assert len(result) == 1
    assert result[0] == UsageData(
        selector=".btn:hover",
        defined_in="",
        used="YES",
        file=str(js_file),
        line_number=1,
        line='document.querySelector(".btn").classList.add("btn:hover");'
    )

def test_analyze_file_php_echo(tmp_path, analyzer, mock_detector):
    """Test PHP file analysis with echo statement."""
    php_file = tmp_path / "test.php"
    php_file.write_text('<?php echo "<div class=\\"container\\">"; ?>')
    selectors = {".container", "div"}

    mock_detector.detect_echo_usage.return_value = [(".container", '<?php echo "<div class=\\"container\\">"; ?>')]
    mock_detector.detect_element_usage.return_value = [("div", '<?php echo "<div class=\\"container\\">"; ?>')]

    result = analyzer.analyze_file(selectors, php_file)
    assert len(result) == 2
    assert UsageData(".container", "", "YES", str(php_file), 1, '<?php echo "<div class=\\"container\\">"; ?>') in result
    assert UsageData("div", "", "YES", str(php_file), 1, '<?php echo "<div class=\\"container\\">"; ?>') in result

def test_analyze_file_combinator(tmp_path, analyzer, mock_detector):
    """Test combinator detection in an HTML file."""
    html_file = tmp_path / "test.html"
    html_file.write_text('<div class="container"><p class="item">Text</p></div>')
    selectors = {".container .item", ".container", ".item", "div", "p"}

    # Mock class detection to return both classes for the line
    mock_detector.detect_class_usage.return_value = [
        (".container", '<div class="container"><p class="item">Text</p></div>'),
        (".item", '<div class="container"><p class="item">Text</p></div>')
    ]
    # Mock element detection with side_effect for sequential element matches
    mock_detector.detect_element_usage.side_effect = [
        [("div", '<div class="container"><p class="item">Text</p></div>')],
        [("p", '<div class="container"><p class="item">Text</p></div>')]
    ]

    result = analyzer.analyze_file(selectors, html_file)
    assert len(result) == 5  # .container, .item, div, p, .container .item
    expected = [
        UsageData(".container", "", "YES", str(html_file), 1, '<div class="container"><p class="item">Text</p></div>'),
        UsageData(".item", "", "YES", str(html_file), 1, '<div class="container"><p class="item">Text</p></div>'),
        UsageData("div", "", "YES", str(html_file), 1, '<div class="container"><p class="item">Text</p></div>'),
        UsageData("p", "", "YES", str(html_file), 1, '<div class="container"><p class="item">Text</p></div>'),
        UsageData(".container .item", "", "YES", str(html_file), 1, '<div class="container"><p class="item">Text</p></div>')
    ]
    for usage in expected:
        assert usage in result

def test_analyze_file_no_duplicates(tmp_path, analyzer, mock_detector):
    """Test that duplicates of the same selector are not added."""
    html_file = tmp_path / "test.html"
    html_file.write_text('<div class="container">')
    selectors = {".container"}

    # Simulate overlapping detection
    mock_detector.detect_class_usage.return_value = [(".container", '<div class="container">')]
    mock_detector.detect_combo_usage.return_value = [(".container", '<div class="container">')]

    result = analyzer.analyze_file(selectors, html_file)
    assert len(result) == 1  # Only one .container entry
    assert result[0] == UsageData(
        selector=".container",
        defined_in="",
        used="YES",
        file=str(html_file),
        line_number=1,
        line='<div class="container">'
    )

def test_analyze_file_file_not_found(tmp_path, analyzer, mock_detector):
    """Test behavior when the file doesn’t exist."""
    nonexistent_file = tmp_path / "nonexistent.html"
    selectors = {".container"}

    result = analyzer.analyze_file(selectors, nonexistent_file)
    assert result == []  # Empty list on error

def test_analyze_file_php_variable_skip(tmp_path, analyzer, mock_detector):
    """Test that PHP variable-only lines are skipped."""
    php_file = tmp_path / "test.php"
    php_file.write_text('$var = "value";\n<div class="container">')
    selectors = {".container"}

    mock_detector.detect_class_usage.return_value = [(".container", '<div class="container">')]

    result = analyzer.analyze_file(selectors, php_file)
    assert len(result) == 1
    assert result[0] == UsageData(
        selector=".container",
        defined_in="",
        used="YES",
        file=str(php_file),
        line_number=2,
        line='<div class="container">'
    )