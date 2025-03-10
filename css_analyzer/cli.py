import argparse
from pathlib import Path
from css_analyzer.css_selector_parser import CSSSelectorParser
from css_analyzer.usage_detector import UsageDetector
from css_analyzer.css_analyzer import CSSAnalyzer
from css_analyzer.csv_generator import CSVGenerator
from css_analyzer.types import UsageData
import os

def main():
    parser = argparse.ArgumentParser(description="CSS Usage Analyzer")
    parser.add_argument("css_file", help="Path to the CSS file")
    parser.add_argument("search_dir", help="Directory to search for HTML, PHP, and JS files")
    parser.add_argument("-o", "--output", default="output.csv", help="Output CSV file path")
    args = parser.parse_args()

    # Parse CSS file
    css_parser = CSSSelectorParser()
    selectors_dict = css_parser.parse(Path(args.css_file))  # {selector: css_file}
    selectors_set = set(selectors_dict.keys())
    css_file_path = str(Path(args.css_file))

    # Initialize analyzer
    detector = UsageDetector()
    analyzer = CSSAnalyzer(detector)

    # Collect files
    files_to_analyze = [
        Path(root) / file
        for root, _, files in os.walk(args.search_dir)
        for file in files if file.endswith(('.html', '.php', '.js'))
    ]

    # Analyze files and accumulate usages
    all_usages = []
    for file_path in files_to_analyze:
        print(f"scanning {file_path}")
        file_usages = analyzer.analyze_file(selectors_set, file_path)
        all_usages.extend(file_usages)

    # Finalize usage data: Include all selectors
    used_selectors = set(u.selector for u in all_usages)
    finalized_usages = all_usages[:]
    for selector in selectors_set:
        if selector not in used_selectors:
            finalized_usages.append(UsageData(
                selector=selector,
                defined_in=css_file_path,
                used="NO",
                file="",
                line_number=0,
                line=""
            ))
        else:
            for usage in finalized_usages:
                if usage.selector == selector:
                    usage.defined_in = css_file_path

    CSVGenerator.generate_csv(args.output, finalized_usages)

if __name__ == "__main__":
    main()