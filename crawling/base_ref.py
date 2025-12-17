from abc import ABC, abstractmethod
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser, Playwright


@dataclass
class Product:
    name: str
    brand: str
    price: str
    url: str
    image_url: str | None = None


class BaseCrawler(ABC):
    """Base class for all crawlers"""

    BASE_URL: str = ""

    def __init__(self, headless: bool = True):
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
        """새 페이지를 생성하고 기본 설정을 적용합니다."""
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        return page

    async def _scroll_page(self, page: Page, scroll_count: int = 3):
        """페이지를 스크롤하여 lazy loading 콘텐츠를 로드합니다."""
        for _ in range(scroll_count):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(1000)

    async def _safe_get_text(self, element, selector: str) -> str:
        """안전하게 텍스트를 추출합니다."""
        elem = await element.query_selector(selector)
        if elem:
            text = await elem.inner_text()
            return text.strip()
        return "Unknown"

    async def _safe_get_attribute(self, element, selector: str, attribute: str) -> str | None:
        """안전하게 속성값을 추출합니다."""
        elem = await element.query_selector(selector)
        if elem:
            return await elem.get_attribute(attribute)
        return None

    @abstractmethod
    async def search_products(self, query: str, max_items: int = 20) -> list[Product]:
        """검색어로 상품을 검색합니다."""
        pass

    @abstractmethod
    async def get_product_detail(self, product_url: str) -> Product | None:
        """상품 상세 페이지에서 정보를 가져옵니다."""
        pass
