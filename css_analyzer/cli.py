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
    parser.add_argument("css_input", help="Path to a CSS file or folder containing CSS files (with --all)")
    parser.add_argument("search_dir", help="Directory to search for HTML, PHP, and JS files")
    parser.add_argument("-o", "--output", default="output.csv", help="Output CSV file path")
    parser.add_argument("-a", "--all", action="store_true", help="Scan a folder for all CSS files instead of a single file")
    args = parser.parse_args()

    # Parse CSS files
    css_parser = CSSSelectorParser()
    css_input_path = Path(args.css_input)
    if args.all:
        if not css_input_path.is_dir():
            raise ValueError(f"With --all, {args.css_input} must be a directory")
        css_files = [f for f in css_input_path.rglob("*.css") if f.is_file()]
        if not css_files:
            raise ValueError(f"No CSS files found in {args.css_input}")
    else:
        if not css_input_path.is_file():
            raise ValueError(f"{args.css_input} must be a CSS file")
        css_files = [css_input_path]

    # Parse all CSS files and combine selectors
    selectors_dict = {}  # {selector: css_file_path}
    for css_file in css_files:
        file_selectors = css_parser.parse(css_file)
        selectors_dict.update(file_selectors)  # Later files override earlier ones if duplicates exist
    selectors_set = set(selectors_dict.keys())

    # Initialize analyzer
    detector = UsageDetector()
    analyzer = CSSAnalyzer(detector)

    # Collect files to analyze
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

    # Finalize usage data
    used_selectors = set(u.selector for u in all_usages)
    finalized_usages = all_usages[:]
    for selector in selectors_set:
        if selector not in used_selectors:
            finalized_usages.append(UsageData(
                selector=selector,
                defined_in=selectors_dict[selector],  # Use specific CSS file path
                used="NO",
                file="",
                line_number=0,
                line=""
            ))
        else:
            for usage in finalized_usages:
                if usage.selector == selector:
                    usage.defined_in = selectors_dict[selector]  # Update with specific CSS file

    # Generate CSV
    CSVGenerator.generate_csv(args.output, finalized_usages)

if __name__ == "__main__":
    main()