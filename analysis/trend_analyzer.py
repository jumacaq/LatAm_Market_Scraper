import pandas as pd

class TrendAnalyzer:
    def __init__(self, db_client):
        self.db = db_client

    def get_summary_stats(self):
        return {
            "total_jobs": 0,
            "new_jobs": 0
        }

    def get_trends_by_sector(self, sectors):
        data = {
            'date': pd.date_range(start='2023-01-01', periods=5),
            'count': [0, 0, 0, 0, 0],
            'sector': ['EdTech'] * 5
        }
        return pd.DataFrame(data)