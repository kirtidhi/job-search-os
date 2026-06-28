import re

class BaseScraper:
    def __init__(self, target_companies, role_preferences, locations):
        self.target_companies = target_companies
        self.role_preferences = [r.lower() for r in role_preferences]
        self.locations = [l.lower() for l in locations]

    def _is_match(self, title, location):
        title = title.lower()
        location = location.lower() if location else ""
        
        # Check if role matches
        role_match = any(
            re.search(r'\b' + re.escape(role) + r'\b', title)
            for role in self.role_preferences
        )
        if not role_match:
            return False
            
        # Check if location matches
        if self.locations:
            loc_match = any(loc in location for loc in self.locations)
            if not loc_match:
                return False
            
        return True
