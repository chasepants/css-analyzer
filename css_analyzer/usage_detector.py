import re
from typing import List, Set, Tuple

class UsageDetector:
    def __init__(self):
        self.echo_pattern = r'echo\s*([\'"])([^\'"]*?(?:\\[\'"].*?)*?)\1\s*;'
        self.class_pattern = r'class=["\']([^"\']*?)["\']'
        self.id_pattern = r'id=["\']([^"\']*?)["\']'
        self.element_pattern = r'<([a-zA-Z][\w-]*)\b[^>]*'
        self.attr_pattern = r'([\w-]+)="\s*([^"]*?)\s*"'
        self.html_tag_pattern = r'<[^>]+class=["\'][^>]*>'
        self.php_var_pattern = r'^\s*\$[\w]+'
        self.style_pattern = r'style=["\'][^"\']*["\']'
        self.js_class_pattern = r'classList\.(add|remove|toggle)\s*\(\s*["\']([^"\']+)["\']'

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

    def detect_pseudo_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        usages = []
        for match in re.finditer(self.style_pattern, line):
            style_content = match.group(0)
            classes = re.findall(self.class_pattern, line)
            for selector in selectors:
                if ':' in selector:
                    base, pseudo = selector.split(':', 1)
                    if base in [f".{cls}" for cls in classes] and f":{pseudo}" in style_content:
                        usages.append((selector, line))
        for match in re.finditer(self.js_class_pattern, line):
            full_class = match.group(2)
            css_selector = f".{full_class}"
            if css_selector in selectors:
                usages.append((css_selector, line))
        return usages

    def detect_echo_usage(self, line: str, selectors: Set[str]) -> List[Tuple[str, str]]:
        usages = []
        for match in re.finditer(self.echo_pattern, line):
            echo_content = match.group(2)
            normalized_content = echo_content.replace('\\"', '"').replace("\\'", "'")
            usages.extend(self.detect_class_usage(normalized_content, selectors))
            usages.extend(self.detect_id_usage(normalized_content, selectors))
            usages.extend(self.detect_element_usage(normalized_content, selectors))
            usages.extend(self.detect_attribute_usage(normalized_content, selectors))
            usages.extend(self.detect_combo_usage(normalized_content, selectors))
            usages.extend(self.detect_pseudo_usage(normalized_content, selectors))
        return [(selector, line) for (selector, _) in usages]