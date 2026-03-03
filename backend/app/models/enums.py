from typing import Literal

Role = Literal["citizen", "authority"]
IssueStatus = Literal["Pending", "Processing", "Completed"]
Category = Literal[
    "Road & Infrastructure",
    "Water & Drainage",
    "Sanitation",
    "Electricity",
    "Public Safety",
    "Other",
]
