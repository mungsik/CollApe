import random
from abc import ABC
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page, Playwright

USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Windows Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Mac Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

@dataclass
class ProductItem:
    """DB 적재용 상품 데이터"""
    brand: str      # 브랜드명
    name: str       # 제품명
    size: str       # 제품 사이즈
    price: str      # 제품 가격
    note: str       # 비고 ex. 마지막 수량, 관부가세 포함
    url: str        # 제품 URL
    images: list    # 제품 이미지 URL 리스트

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
        context = await self.browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Asia/Seoul",
        )
        page = await context.new_page()
        return page

    async def scroll_page(self, page: Page, scroll_pause: float = 2.0):
        """인간다운 스크롤 동작 구현"""
        last_height = await page.evaluate("document.body.scrollHeight")

        while True:
            # 랜덤한 스크롤 동작
            scroll_amount = random.randint(300, 700)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")

            # 자연스러운 대기 시간
            delay = random.uniform(1.0, scroll_pause) * 1000
            await page.wait_for_timeout(delay)

            new_height = await page.evaluate("document.body.scrollHeight")
            current_scroll = await page.evaluate("window.scrollY + window.innerHeight")

            # 페이지 끝에 도달했는지 확인
            if current_scroll >= new_height and new_height == last_height:
                break
            last_height = new_height