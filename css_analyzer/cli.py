import argparse
import os
from .analyzer import CSSAnalyzer

def main():
    parser = argparse.ArgumentParser(
        description='Analyze CSS class usage in HTML/PHP files'
    )
    parser.add_argument(
        'css_file',
        help='Path to the CSS file to analyze'
    )
    parser.add_argument(
        'directory',
        help='Directory to search for HTML/PHP files'
    )
    parser.add_argument(
        '-o', '--output',
        default='css_usage.csv',
        help='Output CSV file path (default: css_usage.csv)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.isfile(args.css_file):
        print(f"Error: CSS file '{args.css_file}' not found")
        return
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found")
        return
    
    print(f"Analyzing {args.css_file} against files in {args.directory}...")
    
    analyzer = CSSAnalyzer(args.css_file, args.directory)
    analyzer.parse_css()
    analyzer.find_usages()
    analyzer.generate_csv(args.output)
    
    print(f"Analysis complete. Results written to {args.output}")

if __name__ == '__main__':
    main()