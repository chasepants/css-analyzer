# css_analyzer/analyzer.py
import csv
import os
from pathlib import Path
import re
from typing import Dict, List, Tuple, Set

class CSSSelectorParser:
    """Parses CSS files to extract selectors."""
    def parse(self, css_file: Path) -> Dict[str, str]:
        """Extract all selectors from the CSS file."""
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Remove comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Match selectors (anything before { and after })
            selector_pattern = r'([^{]+)\s*{[^}]*}'
            matches = re.findall(selector_pattern, content)
            selectors = {}
            for selector in matches:
                # Split comma-separated selectors and clean them
                clean_selectors = [s.strip() for s in selector.split(',') if s.strip()]
                for sel in clean_selectors:
                    selectors[sel] = str(css_file)
            return selectors
        except Exception as e:
            print(f"Error parsing CSS file: {e}")
            raise

class UsageDetector:
    """Detects usage of CSS selectors in files."""
    def __init__(self):
        # Regex patterns for detection
        self.class_pattern = r'class=["\']([^"\']*?)["\']'
        self.id_pattern = r'id=["\']([^"\']*?)["\']'
        self.echo_pattern = r'echo\s*["\'](.*?)["\'];?'
        self.html_tag_pattern = r'<[^>]+class=["\'][^>]*>'
        self.php_var_pattern = r'^\s*\$[\w]+'

    def detect_class_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect class usage in a line."""
        usages = []
        for match in re.finditer(self.class_pattern, line):
            classes = match.group(1).split()
            for css_class in classes:
                selector = f".{css_class}"
                if selector in selectors:
                    usages.append((selector, line))
        return usages

    def detect_id_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect ID usage in a line."""
        usages = []
        for match in re.finditer(self.id_pattern, line):
            css_id = match.group(1)
            selector = f"#{css_id}"
            if selector in selectors:
                usages.append((selector, line))
        return usages

    def detect_echo_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect usage in PHP echo statements."""
        usages = []
        for match in re.finditer(self.echo_pattern, line):
            echo_content = match.group(1)
            # Check classes within echo
            for echo_match in re.finditer(self.class_pattern, echo_content):
                classes = echo_match.group(1).split()
                for css_class in classes:
                    selector = f".{css_class}"
                    if selector in selectors:
                        usages.append((selector, line))
            # Check IDs within echo
            for echo_match in re.finditer(self.id_pattern, echo_content):
                css_id = echo_match.group(1)
                selector = f"#{css_id}"
                if selector in selectors:
                    usages.append((selector, line))
        return usages

class CSSAnalyzer:
    """Orchestrates CSS analysis by delegating parsing and detection tasks."""
    def __init__(self, css_file: str, search_dir: str):
        self.css_file = Path(css_file)
        self.search_dir = Path(search_dir)
        self.selectors = {}  # Dict[selector, file_path]
        self.usages = []    # List[Tuple[selector, file_path, line_num, line]]

    def parse_css(self) -> None:
        """Parse the CSS file to extract selectors."""
        parser = CSSSelectorParser()
        self.selectors = parser.parse(self.css_file)

    def find_usages(self) -> None:
        """Search directory for HTML/PHP files and find selector usages."""
        for root, _, files in os.walk(self.search_dir):
            for file in files:
                if file.endswith(('.html', '.php')):
                    file_path = Path(root) / file
                    self._analyze_file(file_path)

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for selector usage."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            detector = UsageDetector()
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                # Skip PHP variable-only lines to reduce false positives
                if re.match(detector.php_var_pattern, line) and not re.search(detector.html_tag_pattern, line):
                    continue

                # Detect usages
                class_usages = detector.detect_class_usage(line, set(self.selectors.keys()))
                id_usages = detector.detect_id_usage(line, set(self.selectors.keys()))
                echo_usages = detector.detect_echo_usage(line, set(self.selectors.keys()))

                # Collect results
                for selector, usage_line in class_usages + id_usages + echo_usages:
                    self.usages.append((selector, str(file_path), line_num, usage_line))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def generate_csv(self, output_file: str) -> None:
        """Generate CSV report with usage details."""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['CSS Element', 'Defined In', 'Used?', 'File', 'Line Number', 'Line of Code'])
            for element in sorted(self.selectors.keys()):
                defined_in = self.selectors[element]
                element_usages = [u for u in self.usages if u[0] == element]
                is_class_or_id = element.startswith('.') or element.startswith('#')
                if element_usages:
                    for _, file_path, line_num, line in element_usages:
                        writer.writerow([element, defined_in, 'YES', file_path, line_num, line])
                else:
                    status = 'NO' if is_class_or_id else 'UNKNOWN'
                    writer.writerow([element, defined_in, status, '', '', ''])