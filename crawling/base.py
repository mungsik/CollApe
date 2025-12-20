from abc import ABC
from playwright.async_api import async_playwright, Browser, Page, Playwright

class BaseCrawler(ABC):
    """Base class for all crawlers"""

    BASE_URL: str = ""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Browser | None = None
        self.playwright: Playwright | None = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _create_page(self) -> Page:
        page = await self.browser.new_page()
        return page