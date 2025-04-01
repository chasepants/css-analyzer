# tests/test_csv_generator.py
import pytest
from css_analyzer.csv_generator import CSVGenerator
from css_analyzer.types import UsageData
import csv
from pathlib import Path

def test_generate_csv_basic(tmp_path):
    """Test generating a basic CSV with one usage."""
    output_file = tmp_path / "output.csv"
    usages = [
        UsageData(
            selector=".container",
            defined_in="styles.css",
            used="YES",
            file="index.html",
            line_number=1,
            line='<div class="container">Content</div>'
        )
    ]
    CSVGenerator.generate_csv(str(output_file), usages)

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0] == {
            'CSS Element': '.container',
            'Defined In': 'styles.css',
            'Used?': 'YES',
            'File': 'index.html',
            'Line Number': '1',
            'Line of Code': '<div class="container">Content</div>',
            'Usage Commit Date': '',
            'CSS Commit Date': '',
            'CSS Size': '0',
            'Selector Complexity': '0',
            'File Age Days': '0',
            'In Comments': 'False'
        }

def test_generate_csv_multiple_usages(tmp_path):
    """Test generating a CSV with multiple usages."""
    output_file = tmp_path / "output.csv"
    usages = [
        UsageData(
            selector=".container",
            defined_in="styles.css",
            used="YES",
            file="index.html",
            line_number=1,
            line='<div class="container">Content</div>'
        ),
        UsageData(
            selector=".unused",
            defined_in="styles.css",
            used="NO",
            file="",
            line_number=0,
            line=""
        )
    ]
    CSVGenerator.generate_csv(str(output_file), usages)

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2

def test_generate_csv_condensed(tmp_path):
    """Test generating a condensed CSV."""
    output_file = tmp_path / "output.csv"
    usages = [
        UsageData(
            selector=".container",
            defined_in="styles.css",
            used="YES",
            file="",
            line_number=0,
            line="",
            count=3
        )
    ]
    CSVGenerator.generate_csv(str(output_file), usages, condensed=True)

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['Count'] == "3"

def test_generate_csv_special_characters(tmp_path):
    """Test generating a CSV with special characters in fields."""
    output_file = tmp_path / "output.csv"
    usages = [
        UsageData(
            selector=".btn, .btn-primary",
            defined_in="styles,css",
            used="YES",
            file="index.html",
            line_number=2,
            line='<button class="btn, .btn-primary">Click "me"</button>'
        )
    ]

    CSVGenerator.generate_csv(str(output_file), usages)

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0] == {
            'CSS Element': '.btn, .btn-primary',
            'Defined In': 'styles,css',
            'Used?': 'YES',
            'File': 'index.html',
            'Line Number': '2',
            'Line of Code': '<button class="btn, .btn-primary">Click "me"</button>',
            'Usage Commit Date': '',
            'CSS Commit Date': '',
            'CSS Size': '0',
            'Selector Complexity': '0',
            'File Age Days': '0',
            'In Comments': 'False'
        }

def test_generate_csv_empty_list(tmp_path):
    """Test generating a CSV with an empty usage list."""
    output_file = tmp_path / "output.csv"
    usages = []

    CSVGenerator.generate_csv(str(output_file), usages)

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 0
        assert reader.fieldnames == [
            'CSS Element', 'Defined In', 'Used?', 'File', 'Line Number', 'Line of Code',
            'Usage Commit Date', 'CSS Commit Date', 'CSS Size', 'Selector Complexity',
            'File Age Days', 'In Comments'
        ]