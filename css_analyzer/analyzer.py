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
            # Remove CSS comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Pattern to match selectors followed by their rules
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
        # Pattern for PHP echo statements
        self.echo_pattern = r'echo\s*([\'"])(.*?)\1;'
        # Pattern for class attributes
        self.class_pattern = r'class=["\']([^"\']*?)["\']'
        # Pattern for ID attributes
        self.id_pattern = r'id=["\']([^"\']*?)["\']'
        # Pattern for HTML elements (matches partial tags)
        self.element_pattern = r'<([a-zA-Z][\w-]*)\b[^>]*'
        # Pattern for attributes (handles hyphens in names)
        self.attr_pattern = r'([\w-]+)="\s*([^"]*?)\s*"'
        # Pattern to identify HTML tags with classes
        self.html_tag_pattern = r'<[^>]+class=["\'][^>]*>'
        # Pattern to skip standalone PHP variables
        self.php_var_pattern = r'^\s*\$[\w]+'

    def detect_class_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect usage of class selectors (e.g., .my-class)."""
        usages = []
        for match in re.finditer(self.class_pattern, line):
            classes = match.group(1).split()
            for css_class in classes:
                selector = f".{css_class}"
                if selector in selectors:
                    usages.append((selector, line))
        return usages

    def detect_id_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect usage of ID selectors (e.g., #my-id)."""
        usages = []
        for match in re.finditer(self.id_pattern, line):
            css_id = match.group(1)
            selector = f"#{css_id}"
            if selector in selectors:
                usages.append((selector, line))
        return usages

    def detect_element_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect usage of element selectors (e.g., div)."""
        usages = []
        for match in re.finditer(self.element_pattern, line):
            element = match.group(1)
            if element in selectors:
                usages.append((element, line))
        return usages

    def detect_attribute_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect usage of attribute selectors (e.g., [data-type='value'])."""
        usages = []
        if '<' in line and '>' in line:
            for match in re.finditer(self.attr_pattern, line):
                attr_name = match.group(1)
                attr_value = match.group(2).strip()
                selector = f'[{attr_name}="{attr_value}"]'
                if selector in selectors:
                    usages.append((selector, line))
        return usages

    def detect_combo_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect usage of element-class combinations (e.g., p.error)."""
        usages = []
        element_matches = list(re.finditer(self.element_pattern, line))
        class_matches = list(re.finditer(self.class_pattern, line))
        if element_matches and class_matches:
            element = element_matches[0].group(1)
            classes = class_matches[0].group(1).split()
            for css_class in classes:
                selector = f"{element}.{css_class}"
                if selector in selectors:
                    usages.append((selector, line))
        return usages

    def detect_echo_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        """Detect selector usage within PHP echo statements."""
        usages = []
        for match in re.finditer(self.echo_pattern, line):
            echo_content = match.group(2)
            usages.extend(self.detect_class_usage(echo_content, selectors))
            usages.extend(self.detect_id_usage(echo_content, selectors))
            usages.extend(self.detect_element_usage(echo_content, selectors))
            usages.extend(self.detect_attribute_usage(echo_content, selectors))
            usages.extend(self.detect_combo_usage(echo_content, selectors))
 
        return [(selector, line) for (selector, _) in usages]

class CSSAnalyzer:
    def __init__(self, css_file: str, search_dir: str):
        """Initialize with CSS file and directory to search."""
        self.css_file = Path(css_file)
        self.search_dir = Path(search_dir)
        self.selectors = {}
        self.usages = []

    def parse_css(self) -> None:
        """Parse the CSS file to extract selectors."""
        parser = CSSSelectorParser()
        self.selectors = parser.parse(self.css_file)

    def find_usages(self) -> None:
        """Search for selector usages in HTML and PHP files."""
        for root, _, files in os.walk(self.search_dir):
            for file in files:
                if file.endswith(('.html', '.php')):
                    file_path = Path(root) / file
                    self._analyze_file(file_path)

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for selector usages."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            detector = UsageDetector()
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                # Skip lines that are just PHP variable declarations without HTML
                if re.match(detector.php_var_pattern, line) and not re.search(detector.html_tag_pattern, line):
                    continue

                class_usages = detector.detect_class_usage(line, set(self.selectors.keys()))
                id_usages = detector.detect_id_usage(line, set(self.selectors.keys()))
                element_usages = detector.detect_element_usage(line, set(self.selectors.keys()))
                attr_usages = detector.detect_attribute_usage(line, set(self.selectors.keys()))
                combo_usages = detector.detect_combo_usage(line, set(self.selectors.keys()))
                echo_usages = detector.detect_echo_usage(line, set(self.selectors.keys()))

                all_usages = class_usages + id_usages + element_usages + attr_usages + combo_usages + echo_usages
                for selector, usage_line in all_usages:
                    self.usages.append((selector, str(file_path), line_num, usage_line))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def generate_csv(self, output_file: str) -> None:
        """Generate a CSV report of selector usage."""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['CSS Element', 'Defined In', 'Used?', 'File', 'Line Number', 'Line of Code'])
            for element in sorted(self.selectors.keys()):
                defined_in = self.selectors[element]
                element_usages = [u for u in self.usages if u[0] == element]
                is_simple_class_or_id = re.fullmatch(r'\.[a-zA-Z][\w-]*', element) or re.fullmatch(r'#[a-zA-Z][\w-]*', element)
                if element_usages:
                    for _, file_path, line_num, line in element_usages:
                        writer.writerow([element, defined_in, 'YES', file_path, line_num, line])
                else:
                    status = 'NO' if is_simple_class_or_id else 'UNKNOWN'
                    writer.writerow([element, defined_in, status, '', '', ''])