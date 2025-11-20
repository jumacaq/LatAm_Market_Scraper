from scrapy import signals
import random

class RotateUserAgentMiddleware:
    """
    Advanced middleware to rotate User-Agents and properly spoof client hints
    to bypass Cloudflare and Datadome protections on Computrabajo/Multitrabajo.
    """
    def __init__(self):
        self.user_agents = [
            {
                'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'platform': '"Windows"',
                'mobile': '?0'
            },
            {
                'ua': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'platform': '"macOS"',
                'mobile': '?0'
            }
        ]

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        agent_data = random.choice(self.user_agents)
        
        request.headers['User-Agent'] = agent_data['ua']
        
        # Full Chrome Header Spoofing
        request.headers['Sec-Ch-Ua'] = '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"'
        request.headers['Sec-Ch-Ua-Mobile'] = agent_data['mobile']
        request.headers['Sec-Ch-Ua-Platform'] = agent_data['platform']
        
        request.headers['Sec-Fetch-Site'] = 'same-origin'
        request.headers['Sec-Fetch-Mode'] = 'navigate'
        request.headers['Sec-Fetch-User'] = '?1'
        request.headers['Sec-Fetch-Dest'] = 'document'
        
        request.headers['Upgrade-Insecure-Requests'] = '1'
        request.headers['Accept-Language'] = 'es-419,es;q=0.9,en;q=0.8'
        request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        
        # Prevent caching to avoid getting stale 403s
        request.headers['Cache-Control'] = 'max-age=0'
        
        return None