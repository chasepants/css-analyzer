# css_analyzer/css_selector_parser.py
from pathlib import Path
import re
from typing import Dict
import subprocess
import os.path

class CSSSelectorParser:
    def _get_commit_date(self, css_file: Path, selector: str, content: str) -> str:
        """Get the commit date for a selector's first occurrence."""
        try:
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                if selector in line and not line.strip().startswith('/*'):
                    result = subprocess.run(
                        ['git', 'blame', '-L', f'{line_num},{line_num}', '--porcelain', str(css_file)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    for blame_line in result.stdout.splitlines():
                        if blame_line.startswith('committer-time'):
                            timestamp = int(blame_line.split()[1])
                            from datetime import datetime
                            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            return ""
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            return ""

    def _get_file_age(self, css_file: Path) -> int:
        """Get days since the file's last commit."""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ct', str(css_file)],
                capture_output=True,
                text=True,
                check=True
            )
            timestamp = int(result.stdout.strip())
            from datetime import datetime
            days = (datetime.now() - datetime.fromtimestamp(timestamp)).days
            return days
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            return 0

    def parse(self, css_file: Path) -> Dict[str, tuple]:
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            comments = re.findall(r'/\*.*?\*/', content, re.DOTALL)
            content_no_comments = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            selector_pattern = r'([^{]+)\s*{([^}]*)}'
            matches = re.findall(selector_pattern, content_no_comments, re.DOTALL)
            selectors = {}
            file_age = self._get_file_age(css_file)
            for selector, rule_content in matches:
                clean_selectors = [s.strip() for s in selector.split(',') if s.strip()]
                rule_size = len(selector) + len(rule_content) + 4  # Include braces and spacing
                for sel in clean_selectors:
                    commit_date = self._get_commit_date(css_file, sel, content)
                    complexity = len(re.split(r'\s+|[>~+.]', sel))  # Split by combinators and dots
                    in_comments = any(sel in comment for comment in comments)
                    selectors[sel] = (str(css_file), commit_date, rule_size, complexity, file_age, in_comments)
            return selectors
        except Exception as e:
            print(f"Error parsing CSS file: {e}")
            raise