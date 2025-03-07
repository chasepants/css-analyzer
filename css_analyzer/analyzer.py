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
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            selector_pattern = r'([^{]+)\s*{[^}]*}'
            matches = re.findall(selector_pattern, content)
            selectors = {}
            for selector in matches:
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
        self.echo_pattern = r'echo\s*([\'"])(.*?)\1;'
        self.class_pattern = r'class=["\']([^"\']*?)["\']'
        self.id_pattern = r'id=["\']([^"\']*?)["\']'
        self.element_pattern = r'<([a-zA-Z][\w-]*)\b[^>]*'
        self.attr_pattern = r'([\w-]+)="\s*([^"]*?)\s*"'
        self.html_tag_pattern = r'<[^>]+class=["\'][^>]*>'
        self.php_var_pattern = r'^\s*\$[\w]+'

    def detect_class_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        usages = []
        for match in re.finditer(self.class_pattern, line):
            classes = match.group(1).split()
            for css_class in classes:
                selector = f".{css_class}"
                if selector in selectors:
                    usages.append((selector, line))
        return usages

    def detect_id_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        usages = []
        for match in re.finditer(self.id_pattern, line):
            css_id = match.group(1)
            selector = f"#{css_id}"
            if selector in selectors:
                usages.append((selector, line))
        return usages

    def detect_element_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        usages = []
        for match in re.finditer(self.element_pattern, line):
            element = match.group(1)
            if element in selectors:
                usages.append((element, line))
        return usages

    def detect_attribute_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
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
        self.css_file = Path(css_file)
        self.search_dir = Path(search_dir)
        self.selectors = {}
        self.usages = []

    def parse_css(self) -> None:
        parser = CSSSelectorParser()
        self.selectors = parser.parse(self.css_file)

    def find_usages(self) -> None:
        for root, _, files in os.walk(self.search_dir):
            for file in files:
                if file.endswith(('.html', '.php')):
                    file_path = Path(root) / file
                    self._analyze_file(file_path)

    def _analyze_file(self, file_path: Path) -> None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            detector = UsageDetector()
            file_content = ''.join(lines)
            file_selectors = set()
            selector_lines = {}

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
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
                    file_selectors.add(selector)
                    if selector not in selector_lines:
                        selector_lines[selector] = (line_num, usage_line)

            # Check combinators across the entire file
            for selector in self.selectors.keys():
                if ' ' in selector or '>' in selector:
                    parts = re.split(r'\s+|>', selector)
                    parts = [p.strip() for p in parts if p.strip()]
                    if len(parts) > 1:
                        all_present = all(
                            part in file_selectors or
                            (part.startswith('.') and f'class="{part[1:]}"' in file_content) or
                            (part.startswith('#') and f'id="{part[1:]}"' in file_content)
                            for part in parts
                        )
                        if all_present and selector not in [u[0] for u in self.usages]:
                            earliest_line_num = float('inf')
                            earliest_line = ''
                            for part in parts:
                                if part in selector_lines:
                                    part_line_num, part_line = selector_lines[part]
                                    if part_line_num < earliest_line_num:
                                        earliest_line_num = part_line_num
                                        earliest_line = part_line
                            if earliest_line_num != float('inf'):
                                self.usages.append((selector, str(file_path), earliest_line_num, earliest_line))
                            else:
                                self.usages.append((selector, str(file_path), 1, lines[0].strip()))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def generate_csv(self, output_file: str) -> None:
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