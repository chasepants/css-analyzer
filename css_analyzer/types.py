from dataclasses import dataclass

@dataclass
class UsageData:
    selector: str
    defined_in: str
    used: str  # "YES", "NO", or "UNKNOWN"
    file: str
    line_number: int
    line: str
    count: int = 0  # Number of unique files using the selector, used in condensed mode