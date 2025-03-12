# css_analyzer/csv_generator.py
import csv
from typing import List
from .types import UsageData

class CSVGenerator:
    @staticmethod
    def generate_csv(output_file: str, usages: List[UsageData], condensed: bool = False) -> None:
        """
        Generate a CSV file from the list of usage data.

        :param output_file: Path to the output CSV file.
        :param usages: List of UsageData objects.
        :param condensed: If True, output only one row per selector with a count.
        """
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if condensed:
                fieldnames = ['CSS Element', 'Defined In', 'Used?', 'Count']
            else:
                fieldnames = ['CSS Element', 'Defined In', 'Used?', 'File', 'Line Number', 'Line of Code']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for usage in usages:
                row = {
                    'CSS Element': usage.selector,
                    'Defined In': usage.defined_in,
                    'Used?': usage.used
                }
                if condensed:
                    row['Count'] = usage.count
                else:
                    row['File'] = usage.file
                    row['Line Number'] = usage.line_number
                    row['Line of Code'] = usage.line
                writer.writerow(row)