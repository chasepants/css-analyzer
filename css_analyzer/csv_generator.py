import csv
from typing import List
from .types import UsageData

class CSVGenerator:
    @staticmethod
    def generate_csv(output_file: str, usages: List[UsageData]) -> None:
        """
        Generate a CSV file from the list of usage data.

        :param output_file: Path to the output CSV file.
        :param usages: List of UsageData objects.
        """
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['CSS Element', 'Defined In', 'Used?', 'File', 'Line Number', 'Line of Code']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for usage in usages:
                writer.writerow({
                    'CSS Element': usage.selector,
                    'Defined In': usage.defined_in,
                    'Used?': usage.used,
                    'File': usage.file,
                    'Line Number': usage.line_number,
                    'Line of Code': usage.line
                })