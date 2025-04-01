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
    parser.add_argument(
        "--php",
        action="store_true",
        help="Include PHP files in the analysis"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Include HTML files in the analysis"
    )
    parser.add_argument(
        "--js",
        action="store_true",
        help="Include JavaScript files in the analysis"
    )
    args = parser.parse_args()

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

    selectors_dict = {}  # {selector: (path, commit_date, size, complexity, file_age, in_comments)}
    for css_file in css_files:
        file_selectors = css_parser.parse(css_file)
        selectors_dict.update(file_selectors)
    selectors_set = set(selectors_dict.keys())

    detector = UsageDetector()
    analyzer = CSSAnalyzer(detector)

    file_extensions = []
    if args.php or args.html or args.js:
        if args.php:
            file_extensions.append('.php')
        if args.html:
            file_extensions.append('.html')
        if args.js:
            file_extensions.append('.js')
    else:
        file_extensions = ['.html', '.php', '.js']

    files_to_analyze = [
        Path(root) / file
        for root, _, files in os.walk(args.targets)
        for file in files if any(file.endswith(ext) for ext in file_extensions)
    ]

    all_usages = []
    for file_path in files_to_analyze:
        print(f"scanning {file_path}")
        file_usages = analyzer.analyze_file(selectors_set, file_path)
        all_usages.extend(file_usages)

    used_selectors = set(u.selector for u in all_usages)

    if args.condensed:
        selector_data = {}
        for usage in all_usages:
            selector = usage.selector
            if selector not in selector_data:
                path, commit_date, size, complexity, file_age, in_comments = selectors_dict[selector]
                selector_data[selector] = {
                    "defined_in": path,
                    "css_commit_date": commit_date,
                    "css_size": size,
                    "selector_complexity": complexity,
                    "file_age_days": file_age,
                    "in_comments": in_comments,
                    "used": usage.used,
                    "files": set(),
                    "count": 0,
                    "usage_commit_date": usage.usage_commit_date
                }
            if usage.used == "YES":
                selector_data[selector]["files"].add(usage.file)
                selector_data[selector]["count"] = len(selector_data[selector]["files"])
                if usage.usage_commit_date > selector_data[selector]["usage_commit_date"]:
                    selector_data[selector]["usage_commit_date"] = usage.usage_commit_date

        finalized_usages = []
        for selector in selectors_set:
            if selector in selector_data:
                data = selector_data[selector]
                if not args.unused or data["used"] == "NO":
                    finalized_usages.append(UsageData(
                        selector=selector,
                        defined_in=data["defined_in"],
                        used=data["used"],
                        file="",
                        line_number=0,
                        line="",
                        count=data["count"],
                        usage_commit_date=data["usage_commit_date"],
                        css_commit_date=data["css_commit_date"],
                        css_size=data["css_size"],
                        selector_complexity=data["selector_complexity"],
                        file_age_days=data["file_age_days"],
                        in_comments=data["in_comments"]
                    ))
            elif not args.unused or selector not in used_selectors:
                path, commit_date, size, complexity, file_age, in_comments = selectors_dict[selector]
                finalized_usages.append(UsageData(
                    selector=selector,
                    defined_in=path,
                    used="NO",
                    file="",
                    line_number=0,
                    line="",
                    count=0,
                    usage_commit_date="",
                    css_commit_date=commit_date,
                    css_size=size,
                    selector_complexity=complexity,
                    file_age_days=file_age,
                    in_comments=in_comments
                ))
    else:
        finalized_usages = all_usages[:]
        for selector in selectors_set:
            if selector not in used_selectors:
                path, commit_date, size, complexity, file_age, in_comments = selectors_dict[selector]
                finalized_usages.append(UsageData(
                    selector=selector,
                    defined_in=path,
                    used="NO",
                    file="",
                    line_number=0,
                    line="",
                    css_commit_date=commit_date,
                    css_size=size,
                    selector_complexity=complexity,
                    file_age_days=file_age,
                    in_comments=in_comments
                ))
            else:
                for usage in finalized_usages:
                    if usage.selector == selector:
                        path, commit_date, size, complexity, file_age, in_comments = selectors_dict[selector]
                        usage.defined_in = path
                        usage.css_commit_date = commit_date
                        usage.css_size = size
                        usage.selector_complexity = complexity
                        usage.file_age_days = file_age
                        usage.in_comments = in_comments
        if args.unused:
            finalized_usages = [u for u in finalized_usages if u.used == "NO"]

    CSVGenerator.generate_csv(args.output, finalized_usages, condensed=args.condensed)

if __name__ == "__main__":
    main()