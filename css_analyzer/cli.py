# css_analyzer/cli.py
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
    parser.add_argument(
        "--css",
        required=True,
        help="Path to a CSS file or folder containing CSS files (with --all)"
    )
    parser.add_argument(
        "--targets",
        required=True,
        help="Directory to search for HTML, PHP, and JS files"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.csv",
        help="Output CSV file path (default: output.csv)"
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Scan a folder for all CSS files instead of a single file"
    )
    parser.add_argument(
        "-c",
        "--condensed",
        action="store_true",
        help="Condense duplicate selectors into one row with a usage count"
    )
    parser.add_argument(
        "-u",
        "--unused",
        action="store_true",
        help="Show only unused selectors in the output"
    )
    args = parser.parse_args()

    # Parse CSS files
    css_parser = CSSSelectorParser()
    css_input_path = Path(args.css)
    if args.all:
        if not css_input_path.is_dir():
            raise ValueError(f"With --all, {args.css} must be a directory")
        css_files = [f for f in css_input_path.rglob("*.css") if f.is_file()]
        if not css_files:
            raise ValueError(f"No CSS files found in {args.css}")
    else:
        if not css_input_path.is_file():
            raise ValueError(f"{args.css} must be a CSS file")
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
        for root, _, files in os.walk(args.targets)
        for file in files if file.endswith(('.html', '.php', '.js'))
    ]

    # Analyze files and accumulate usages
    all_usages = []
    for file_path in files_to_analyze:
        print(f"scanning {file_path}")
        file_usages = analyzer.analyze_file(selectors_set, file_path)
        all_usages.extend(file_usages)

    # Define used selectors once, before mode-specific logic
    used_selectors = set(u.selector for u in all_usages)

    # Finalize usage data
    if args.condensed:
        # Aggregate duplicates into one entry per selector with a file count
        selector_data = {}
        for usage in all_usages:
            selector = usage.selector
            if selector not in selector_data:
                selector_data[selector] = {
                    "defined_in": selectors_dict[selector],
                    "used": usage.used,
                    "files": set(),
                    "count": 0
                }
            if usage.used == "YES":
                selector_data[selector]["files"].add(usage.file)
                selector_data[selector]["count"] = len(selector_data[selector]["files"])

        # Build finalized usages with counts
        finalized_usages = []
        for selector in selectors_set:
            if selector in selector_data:
                data = selector_data[selector]
                if not args.unused or data["used"] == "NO":  # Include only unused if --unused is set
                    finalized_usages.append(UsageData(
                        selector=selector,
                        defined_in=data["defined_in"],
                        used=data["used"],
                        file="",
                        line_number=0,
                        line="",
                        count=data["count"]
                    ))
            elif not args.unused or selector not in used_selectors:
                finalized_usages.append(UsageData(
                    selector=selector,
                    defined_in=selectors_dict[selector],
                    used="NO",
                    file="",
                    line_number=0,
                    line="",
                    count=0
                ))
    else:
        # Original detailed mode
        finalized_usages = all_usages[:]
        for selector in selectors_set:
            if selector not in used_selectors:
                finalized_usages.append(UsageData(
                    selector=selector,
                    defined_in=selectors_dict[selector],
                    used="NO",
                    file="",
                    line_number=0,
                    line=""
                ))
            else:
                for usage in finalized_usages:
                    if usage.selector == selector:
                        usage.defined_in = selectors_dict[selector]
        if args.unused:
            finalized_usages = [u for u in finalized_usages if u.used == "NO"]

    # Generate CSV
    CSVGenerator.generate_csv(args.output, finalized_usages, condensed=args.condensed)

if __name__ == "__main__":
    main()