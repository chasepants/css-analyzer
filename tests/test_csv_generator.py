# tests/test_csv_generator.py
import pytest
from pathlib import Path
import csv
from css_analyzer.csv_generator import CSVGenerator
from css_analyzer.types import UsageData

def test_generate_csv_basic(tmp_path):
    """Test generating a CSV with basic usage data."""
    output_file = tmp_path / "output.csv"
    usages = [
        UsageData(
            selector=".container",
            defined_in="styles.css",
            used="YES",
            file="index.html",
            line_number=1,
            line='<div class="container">'
        ),
        UsageData(
            selector="#header",
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
        assert rows[0] == {
            'CSS Element': '.container',
            'Defined In': 'styles.css',
            'Used?': 'YES',
            'File': 'index.html',
            'Line Number': '1',
            'Line of Code': '<div class="container">'
        }
        assert rows[1] == {
            'CSS Element': '#header',
            'Defined In': 'styles.css',
            'Used?': 'NO',
            'File': '',
            'Line Number': '0',
            'Line of Code': ''
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
        # Check headers are still written
        assert reader.fieldnames == ['CSS Element', 'Defined In', 'Used?', 'File', 'Line Number', 'Line of Code']

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
            'Line of Code': '<button class="btn, .btn-primary">Click "me"</button>'
        }

def test_generate_csv_overwrites_existing_file(tmp_path):
    """Test that generating a CSV overwrites an existing file."""
    output_file = tmp_path / "output.csv"
    # Create an existing file with different content
    output_file.write_text("Old content")
    usages = [
        UsageData(
            selector=".container",
            defined_in="styles.css",
            used="YES",
            file="index.html",
            line_number=1,
            line='<div class="container">'
        )
    ]

    CSVGenerator.generate_csv(str(output_file), usages)

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Old content" not in content  # Old content is overwritten
        reader = csv.DictReader(content.splitlines())
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['CSS Element'] == '.container'

def test_generate_csv_directory_not_found(tmp_path):
    """Test generating a CSV when the output directory doesn’t exist."""
    output_file = tmp_path / "nonexistent" / "output.csv"
    usages = [
        UsageData(
            selector=".container",
            defined_in="styles.css",
            used="YES",
            file="index.html",
            line_number=1,
            line='<div class="container">'
        )
    ]

    with pytest.raises(FileNotFoundError):
        CSVGenerator.generate_csv(str(output_file), usages)