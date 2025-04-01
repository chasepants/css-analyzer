from pathlib import Path
import re
from typing import List, Set
from .usage_detector import UsageDetector
from .types import UsageData
import subprocess

class CSSAnalyzer:
    def __init__(self, detector: UsageDetector):
        self.detector = detector

    def _get_commit_date(self, file_path: Path, line_num: int) -> str:
        try:
            result = subprocess.run(
                ['git', 'blame', '-L', f'{line_num},{line_num}', '--porcelain', str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.splitlines():
                if line.startswith('committer-time'):
                    timestamp = int(line.split()[1])
                    from datetime import datetime
                    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            return ""
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            return ""

    def _add_usage(self, usages: List[UsageData], seen: Set[tuple], selector: str, file_path: str, line_num: int, line: str) -> None:
        key = (selector, file_path, line_num)
        if key not in seen:
            seen.add(key)
            commit_date = self._get_commit_date(Path(file_path), line_num)
            usages.append(UsageData(
                selector=selector,
                defined_in="",  # Filled by CLI
                used="YES",
                file=file_path,
                line_number=line_num,
                line=line.strip(),
                usage_commit_date=commit_date
            ))

    def analyze_file(self, selectors: Set[str], file_path: Path) -> List[UsageData]:
        usages = []
        seen = set()
        file_str = str(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            file_content = ''.join(lines)
            file_selectors = set()
            selector_lines = {}

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if file_path.suffix == '.php' and re.match(self.detector.php_var_pattern, line) and not re.search(self.detector.html_tag_pattern, line):
                    continue

                all_usages = (
                    self.detector.detect_class_usage(line, selectors) +
                    self.detector.detect_id_usage(line, selectors) +
                    self.detector.detect_element_usage(line, selectors) +
                    self.detector.detect_attribute_usage(line, selectors) +
                    self.detector.detect_combo_usage(line, selectors) +
                    (self.detector.detect_echo_usage(line, selectors) if file_path.suffix == '.php' else []) +
                    self.detector.detect_pseudo_usage(line, selectors)
                )

                for selector, usage_line in all_usages:
                    self._add_usage(usages, seen, selector, file_str, line_num, usage_line)
                    file_selectors.add(selector)
                    if selector not in selector_lines:
                        selector_lines[selector] = (line_num, usage_line)

                for match in re.finditer(self.detector.element_pattern, line):
                    element = match.group(1)
                    if element in selectors:
                        self._add_usage(usages, seen, element, file_str, line_num, line)
                        file_selectors.add(element)
                        if element not in selector_lines:
                            selector_lines[element] = (line_num, line)

            for selector in selectors:
                if ' ' in selector or '>' in selector:
                    parts = [p.strip() for p in re.split(r'\s+|>', selector) if p.strip()]
                    if len(parts) > 1:
                        all_present = all(
                            part in file_selectors or
                            (part.startswith('.') and f'class="{part[1:]}"' in file_content) or
                            (part.startswith('#') and f'id="{part[1:]}"' in file_content)
                            for part in parts
                        )
                        if all_present:
                            target_part = parts[0] if '>' not in selector else parts[0]
                            line_num, line = selector_lines.get(target_part, (1, lines[0].strip()))
                            self._add_usage(usages, seen, selector, file_str, line_num, line)
                elif ':' in selector:
                    base_selector = selector.split(':')[0]
                    if base_selector in file_selectors:
                        line_num, line = selector_lines[base_selector]
                        self._add_usage(usages, seen, selector, file_str, line_num, line)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

        return usages