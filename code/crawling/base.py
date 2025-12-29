from abc import ABC
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page, Playwright

@dataclass
class ProductItem:
    """DB 적재용 상품 데이터"""
    brand: str      # 브랜드명
    name: str       # 제품명
    size: str       # 제품 사이즈
    price: str      # 제품 가격
    note: str       # 비고 ex. 마지막 수량, 관부가세 포함
    url: str        # 제품 URL

class BaseCrawler(ABC):
    """크롤러 기본 메소드 정의"""

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