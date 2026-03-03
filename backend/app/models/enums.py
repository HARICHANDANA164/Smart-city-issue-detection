from typing import Literal

Role = Literal["citizen", "authority"]
IssueStatus = Literal["Pending", "Not Started", "Completed"]
Category = Literal[
    "Road & Infrastructure",
    "Water & Drainage",
    "Sanitation",
    "Electricity",
    "Public Safety",
    "Other",
]
