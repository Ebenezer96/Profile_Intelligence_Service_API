import re


COUNTRY_MAP = {
    "angola": "AO",
    "benin": "BJ",
    "cameroon": "CM",
    "ethiopia": "ET",
    "ghana": "GH",
    "india": "IN",
    "kenya": "KE",
    "nigeria": "NG",
    "rwanda": "RW",
    "senegal": "SN",
    "south africa": "ZA",
    "tanzania": "TZ",
    "uganda": "UG",
    "united kingdom": "GB",
    "zambia": "ZM",
}


def parse_natural_language_query(query: str) -> dict:
    if not query or not query.strip():
        return {}

    text = query.strip().lower()
    filters = {}

    has_male = bool(re.search(r"\bmale\b|\bmales\b", text))
    has_female = bool(re.search(r"\bfemale\b|\bfemales\b", text))

    if has_male and not has_female:
        filters["gender"] = "male"
    elif has_female and not has_male:
        filters["gender"] = "female"

    if re.search(r"\bchild\b|\bchildren\b", text):
        filters["age_group"] = "child"
    elif re.search(r"\bteenager\b|\bteenagers\b", text):
        filters["age_group"] = "teenager"
    elif re.search(r"\badult\b|\badults\b", text):
        filters["age_group"] = "adult"
    elif re.search(r"\bsenior\b|\bseniors\b", text):
        filters["age_group"] = "senior"

    if re.search(r"\byoung\b", text):
        filters["min_age"] = 16
        filters["max_age"] = 24

    above_match = re.search(r"\b(?:above|over)\s+(\d+)\b", text)
    if above_match:
        filters["min_age"] = int(above_match.group(1))

    below_match = re.search(r"\b(?:below|under)\s+(\d+)\b", text)
    if below_match:
        filters["max_age"] = int(below_match.group(1))

    for country_name, country_code in COUNTRY_MAP.items():
        if f"from {country_name}" in text or country_name in text:
            filters["country_id"] = country_code
            break

    return filters