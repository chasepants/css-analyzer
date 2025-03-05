# css_analyzer/analyzer.py
import csv
import os
from pathlib import Path
import re
from typing import Dict, List, Tuple

class CSSAnalyzer:
    def __init__(self, css_file: str, search_dir: str):
        self.css_file = Path(css_file)
        self.search_dir = Path(search_dir)
        self.css_definitions = {}  # Dict[element_type:element_name, file_path]
        self.css_usage = []  # List[Tuple[element, file_path, line_num, line]]

    def parse_css(self) -> None:
        """Parse CSS file and extract class and ID definitions."""
        try:
            with open(self.css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Class pattern
            class_pattern = r'\.([a-zA-Z][\w-]*)\s*(?:{[^}]*}|\s*,)'
            classes = re.findall(class_pattern, content)
            for css_class in classes:
                self.css_definitions[f"class:{css_class}"] = str(self.css_file)
            # ID pattern
            id_pattern = r'#([a-zA-Z][\w-]*)\s*(?:{[^}]*}|\s*,)'
            ids = re.findall(id_pattern, content)
            for css_id in ids:
                self.css_definitions[f"id:{css_id}"] = str(self.css_file)
        except Exception as e:
            print(f"Error parsing CSS file: {e}")
            raise

    def find_usages(self) -> None:
        """Search directory for HTML/PHP files and find element usages."""
        for root, _, files in os.walk(self.search_dir):
            for file in files:
                if file.endswith(('.html', '.php')):
                    file_path = Path(root) / file
                    self._analyze_file(file_path)

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a file for CSS class and ID usage."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Patterns for usage
            class_pattern = r'class=["\']([^"\']*?)["\']'
            id_pattern = r'id=["\']([^"\']*?)["\']'
            echo_pattern = r'echo\s*["\'](.*?)["\'];?'
            html_tag_pattern = r'<[^>]+class=["\'][^>]*>'
            php_var_pattern = r'^\s*\$[\w]+'  # Standalone PHP variable

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                # Skip lines that are purely PHP variables (prefilter false positives)
                if re.match(php_var_pattern, line) and not re.search(html_tag_pattern, line):
                    continue

                # Static HTML class attributes
                for match in re.finditer(class_pattern, line):
                    classes = match.group(1).split()
                    for css_class in classes:
                        element = f"class:{css_class}"
                        if element in self.css_definitions:
                            self.css_usage.append((element, str(file_path), line_num, line))

                # Static HTML ID attributes
                for match in re.finditer(id_pattern, line):
                    css_id = match.group(1)
                    element = f"id:{css_id}"
                    if element in self.css_definitions:
                        self.css_usage.append((element, str(file_path), line_num, line))

                # PHP echo statements
                for match in re.finditer(echo_pattern, line):
                    echo_content = match.group(1)
                    # Check for class attributes within echo
                    for echo_match in re.finditer(class_pattern, echo_content):
                        classes = echo_match.group(1).split()
                        for css_class in classes:
                            element = f"class:{css_class}"
                            if element in self.css_definitions:
                                self.css_usage.append((element, str(file_path), line_num, line))
                    # Check for ID attributes within echo
                    for echo_match in re.finditer(id_pattern, echo_content):
                        css_id = echo_match.group(1)
                        element = f"id:{css_id}"
                        if element in self.css_definitions:
                            self.css_usage.append((element, str(file_path), line_num, line))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def generate_csv(self, output_file: str) -> None:
        """Generate CSV report with one row per usage, including unused elements and Used? column."""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['CSS Element', 'Defined In', 'Used?', 'File', 'Line Number', 'Line of Code'])
            # Write all defined elements, even if unused
            for element in sorted(self.css_definitions.keys()):
                defined_in = self.css_definitions[element]
                usages = [u for u in self.css_usage if u[0] == element]
                if usages:
                    for _, file_path, line_num, line in usages:
                        writer.writerow([element, defined_in, 'YES', file_path, line_num, line])
                else:
                    writer.writerow([element, defined_in, 'NO', '', '', ''])  # Empty usage