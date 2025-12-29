import random
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from fake_useragent import UserAgent

class BrowserManager:
    def __init__(self, headless=True):
        self.headless = headless
        self.ua = UserAgent()

    async def get_context_and_page(self, playwright):
        # Rotating User-Agent
        user_agent = self.ua.random
        
        # Randomize Viewport slightly
        width = random.randint(1366, 1920)
        height = random.randint(768, 1080)
        
        browser = await playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"] # Basic stealth arg
        )
        
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={'width': width, 'height': height},
            locale='fr-FR',
            timezone_id='Africa/Casablanca',
            permissions=['geolocation'],
            geolocation={'latitude': 31.7917, 'longitude': -7.0926}, # Morocco center
            device_scale_factor=random.choice([1, 1.25, 1.5]) 
        )
        
        page = await context.new_page()
        
        # Apply Stealth
        stealth_config = Stealth()
        await stealth_config.apply_stealth_async(page)
        
        return browser, context, page

    async def human_delay(self):
        # Random delay 1-4 seconds
        await asyncio.sleep(random.uniform(1, 4))

    async def simulate_human_behavior(self, page):
        # Mouse movements and scrolling
        await self.human_delay()
        
        # Random mouse moves
        for _ in range(random.randint(2, 5)):
             await page.mouse.move(random.randint(0, 500), random.randint(0, 500))
             await asyncio.sleep(0.1)
             
        # Scroll down
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await self.human_delay()
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.human_delay()
