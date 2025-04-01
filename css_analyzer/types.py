from dataclasses import dataclass

@dataclass
class UsageData:
    selector: str
    defined_in: str
    used: str  # "YES", "NO"
    file: str
    line_number: int
    line: str
    count: int = 0
    css_commit_date: str = ""       # ISO date (e.g., "2025-03-20")
    usage_commit_date: str = ""     # ISO date or empty
    css_size: int = 0               # Bytes of the CSS rule
    selector_complexity: int = 0    # Number of parts in selector
    file_age_days: int = 0          # Days since file last modified
    in_comments: bool = False       # True if in CSS comment