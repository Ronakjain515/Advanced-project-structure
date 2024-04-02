CourseLevel = (
    ("BEGINNER", "Beginner"),
    ("INTERMEDIATE", "Intermediate"),
    ("EXPERT", "Expert"),
)
AudioLanguage = (
    ("ENGLISH", "English"),
)
CourseStatusChoices = (
    ("DRAFT", "Draft"),
    ("Pending", "Pending"),
    ("PUBLISHED", "Published"),
    ("UN_PUBLISHED", "Un-Published"),
)
DurationTypes = {
    "4": {
        "max": "04:00:00"
    },
    "4-7": {
        "min": "04:00:00",
        "max": "07:00:00"
    },
    "7-20": {
        "min": "07:00:00",
        "max": "20:00:00"
    },
    "20": {
        "min": "20:00:00"
    }
}