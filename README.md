# CSS Analyzer

A tool to analyze CSS selector usage across HTML, PHP, and JavaScript files, helping you identify unused or redundant styles.

## Installation

1. Clone the repository:
```bash
    git clone https://github.com/yourusername/css-analyzer.git
    cd css-analyzer
```

2. Set up a virtual environment and install dependencies
```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
```

## Usage

Run the tool using the css-analyzer command (installed via pip install -e . if set up as a package) or directly with python -m css_analyzer.cli.

### Options

- --css <path> (required): Path to a single CSS file or a folder containing CSS files (use with --all).
- --targets <directory> (required): Directory to search for HTML, PHP, and JS files to analyze for CSS usage.
- -o, --output <file> (optional): Output CSV file path (default: output.csv).
- -a, --all (optional): Scan a folder for all .css files instead of a single file.

### Examples

Analyze a Single CSS File:
```bash 
    css-analyzer --css examples/main.css --targets examples/src -o output.csv
```
- Analyzes selectors from main.css against files in examples/src.

Analyze Multiple CSS Files:
```bash 
    css-analyzer --css examples --targets examples/src -o output.csv -a
```
- Scans all .css files in examples/ (e.g., main.css, extra.css) against examples/src.

## Output

The tool generates a CSV file with the following columns:

    CSS Element: The CSS selector (e.g., .container, #header, div).
    Defined In: The file path where the selector is defined (e.g., examples/main.css).
    Used?: YES if the selector is used in the target files, NO if unused.
    File: The file where the selector is used (empty if unused).
    Line Number: The line number where the selector is used (0 if unused).
    Line of Code: The specific line of code where the selector is used (empty if unused).

Example output.csv from the second command above:

```
    CSS Element,Defined In,Used?,File,Line Number,Line of Code
    .container,examples/main.css,YES,examples/src/index.html,1,<div class="container">Main content</div>
    .header,examples/extra.css,YES,examples/src/script.js,1,document.querySelector('.header').style.display = 'block';
    .unused,examples/main.css,NO,,0,
    .footer,examples/extra.css,NO,,0,
```

# Development

Tests: Run ```pytest tests/ -v``` to execute all unit tests.
Coverage: Use ```coverage run -m pytest``` followed by coverage report to check test coverage.
Examples: The examples/ directory contains sample files (main.css, extra.css, src/index.html, src/script.js) for testing.

## Setting Up Git Hooks

To enforce test and coverage checks before pushing:

1. Copy the pre-push hook:
```bash
    cp scripts/pre-push.sh .git/hooks/pre-push
    chmod +x .git/hooks/pre-push
```

2. Push your changes. The hook runs pytest and requires ≥80% test coverage.