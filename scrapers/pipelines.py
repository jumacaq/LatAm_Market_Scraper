from database.supabase_client import SupabaseClient
from etl.cleaners import TextCleaner
import logging

class SupabasePipeline:
    def __init__(self):
        self.cleaner = TextCleaner()
        try:
            self.client = SupabaseClient()
            logging.info("✅ Connected to Supabase successfully.")
        except Exception as e:
            logging.error(f"❌ Could not connect to Supabase: {e}")
            self.client = None

    def process_item(self, item, spider):
        # Clean data
        item['title'] = self.cleaner.clean_title(item.get('title'))
        item['description'] = self.cleaner.remove_html(item.get('description'))
        
        # Save to DB
        if self.client:
            try:
                # Convert item to dict for insertion
                data = dict(item)
                # Remove None values
                data = {k: v for k, v in data.items() if v is not None}
                
                self.client.upsert_job(data)
                logging.info(f"✅ Saved to DB: {item.get('title')}")
            except Exception as e:
                error_msg = str(e)
                logging.error(f"❌ DB ERROR for '{item.get('title')}': {error_msg}")
        else:
            logging.warning(f"⚠️ Skipped DB save (No Connection): {item.get('title')}")
            
        return item