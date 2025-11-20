class SeniorityNormalizer:
    def normalize(self, title):
        title = title.lower()
        if 'senior' in title or 'sr.' in title:
            return 'Senior'
        elif 'lead' in title or 'principal' in title:
            return 'Lead'
        elif 'junior' in title or 'intern' in title:
            return 'Junior'
        return 'Mid-Level'