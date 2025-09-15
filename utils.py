import re
from typing import Dict, Optional
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------------
# Query processing helpers
# -----------------------------------------------------------------------------------

def extract_locations_and_date(query: str) -> Dict[str, Optional[str]]:
    """Extract departure, arrival locations and date from user query"""
    query_lower = query.lower()

    # Common Pakistani cities for railway
    cities = [
        "karachi", "lahore", "islamabad", "rawalpindi", "faisalabad",
        "multan", "peshawar", "quetta", "hyderabad", "sukkur",
        "bahawalpur", "gujranwala", "sialkot", "sargodha", "jhang"
    ]

    departure = None
    arrival = None
    date = None

    # Extract cities mentioned in query
    found_cities = [city for city in cities if city in query_lower]

    # Simple patterns for departure/arrival detection
    if " from " in query_lower and " to " in query_lower:
        parts = query_lower.split(" from ")
        if len(parts) > 1:
            from_part = parts[1].split(" to ")[0].strip()
            departure = from_part.title()

            to_parts = parts[1].split(" to ")
            if len(to_parts) > 1:
                arrival = to_parts[1].split()[0].strip().title()

    elif " to " in query_lower:
        if found_cities:
            arrival = found_cities[-1].title()
            if len(found_cities) > 1:
                departure = found_cities[0].title()

    # Extract date patterns
    if "today" in query_lower:
        date = datetime.now().strftime("%Y-%m-%d")
    elif "tomorrow" in query_lower:
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # Look for date patterns
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, query)
            if match:
                date_str = match.group()
                try:
                    for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"]:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            date = parsed_date.strftime("%Y-%m-%d")
                            break
                        except Exception:
                            continue
                except Exception:
                    pass

    return {
        "departure": departure,
        "arrival": arrival,
        "date": date or datetime.now().strftime("%Y-%m-%d")
    }