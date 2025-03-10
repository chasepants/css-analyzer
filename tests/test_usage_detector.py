import pytest
from css_analyzer.usage_detector import UsageDetector

@pytest.fixture
def detector():
    """Fixture to provide a fresh UsageDetector instance."""
    return UsageDetector()

def test_detect_class_usage(detector):
    """Test detecting class selectors in a line."""
    line = '<div class="container main">Content</div>'
    selectors = {".container", ".main", ".unused"}
    result = detector.detect_class_usage(line, selectors)
    expected = [
        (".container", line),
        (".main", line)
    ]
    assert result == expected

def test_detect_id_usage(detector):
    """Test detecting ID selectors in a line."""
    line = '<div id="header">Content</div>'
    selectors = {"#header", "#footer"}
    result = detector.detect_id_usage(line, selectors)
    expected = [("#header", line)]
    assert result == expected

def test_detect_element_usage(detector):
    """Test detecting element selectors in a line."""
    line = '<div class="container">Content</div>'
    selectors = {"div", "span"}
    result = detector.detect_element_usage(line, selectors)
    expected = [("div", line)]
    assert result == expected

def test_detect_attribute_usage(detector):
    """Test detecting attribute selectors in a line."""
    line = '<button data-type="submit" class="btn">Click</button>'
    selectors = {'[data-type="submit"]', '[data-type="reset"]'}
    result = detector.detect_attribute_usage(line, selectors)
    expected = [('[data-type="submit"]', line)]
    assert result == expected

def test_detect_attribute_usage_no_tags(detector):
    """Test attribute detection skips lines without tags."""
    line = 'data-type="submit"'
    selectors = {'[data-type="submit"]'}
    result = detector.detect_attribute_usage(line, selectors)
    assert result == []  # No <tag> present

def test_detect_combo_usage(detector):
    """Test detecting combination selectors (element + class)."""
    line = '<div class="container main">Content</div>'
    selectors = {"div.container", "div.main", "span.container"}
    result = detector.detect_combo_usage(line, selectors)
    expected = [
        ("div.container", line),
        ("div.main", line)
    ]
    assert result == expected

def test_detect_combo_usage_no_combo(detector):
    """Test combo detection when no combination exists."""
    line = '<div>Content</div>'
    selectors = {"div.container"}
    result = detector.detect_combo_usage(line, selectors)
    assert result == []  # No class present

def test_detect_pseudo_usage_inline_style(detector):
    """Test detecting pseudo-class usage in inline styles."""
    line = '<div class="btn" style=":hover { color: red; }">Hover</div>'
    selectors = {".btn:hover", ".btn:active"}
    result = detector.detect_pseudo_usage(line, selectors)
    expected = [(".btn:hover", line)]
    assert result == expected

def test_detect_pseudo_usage_js_classlist(detector):
    """Test detecting pseudo-class usage in JS classList methods."""
    line = 'element.classList.add("btn:hover");'
    selectors = {".btn:hover", ".btn:active"}
    result = detector.detect_pseudo_usage(line, selectors)
    expected = [(".btn:hover", line)]
    assert result == expected

def test_detect_pseudo_usage_no_match(detector):
    """Test pseudo detection with no matching usage."""
    line = '<div class="btn">No pseudo</div>'
    selectors = {".btn:hover"}
    result = detector.detect_pseudo_usage(line, selectors)
    assert result == []  # No pseudo-class usage

def test_detect_echo_usage(detector):
    """Test detecting selectors in PHP echo statements."""
    line = 'echo "<div class=\\"container\\" id=\\"header\\">Content</div>";'
    selectors = {".container", "#header", ".main"}
    result = detector.detect_echo_usage(line, selectors)
    expected = [
        (".container", line),
        ("#header", line)
    ]
    assert result == expected

def test_detect_echo_usage_no_selectors(detector):
    """Test echo detection with no matching selectors."""
    line = 'echo "<span>Plain text</span>";'
    selectors = {".container"}
    result = detector.detect_echo_usage(line, selectors)
    assert result == []  # No selectors matched

def test_detect_class_usage_empty_line(detector):
    """Test class detection with an empty line."""
    line = ""
    selectors = {".container"}
    result = detector.detect_class_usage(line, selectors)
    assert result == []  # No classes to detect