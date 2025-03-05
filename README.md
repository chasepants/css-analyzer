# CSS Analyzer

A command-line tool to analyze CSS class usage in HTML/PHP files.

## Installation

Install the tool using pip: pip install css-analyzer

## Usage

Run the tool with the following command: css-analyzer <css_file> <directory> [-o output.csv]

### Arguments
- css_file: Path to the CSS file to analyze
- directory: Directory containing HTML/PHP files to search
- -o/--output: Output CSV file path (default: css_usage.csv)

## Output
The tool generates a CSV file with the following columns:
- CSS Element: The CSS class name
- Defined In: File where the class is defined
- Used In: Comma-separated list of files where the class is used