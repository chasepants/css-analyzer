from pathlib import Path
import re
from typing import Dict

class CSSSelectorParser:
    def parse(self, css_file: Path) -> Dict[str, str]:
        """
        Parse the CSS file and return a dictionary of selectors mapped to their file paths.

        :param css_file: Path to the CSS file
        :return: Dictionary with selectors as keys and file paths as values
        """
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