import asyncio
from crawling.base import BaseCrawler


class FarfetchCrawler(BaseCrawler):

    BASE_URL = "https://www.farfetch.com/kr"

    async def goto_main(self):
        page = await self._create_page()
        await page.goto(self.BASE_URL)
        print(f"메인 페이지 접속 완료: {self.BASE_URL}")
        return page

async def main():
    async with FarfetchCrawler(headless=False) as crawler:
        page = await crawler.goto_main()
        await page.wait_for_timeout(3000)  

if __name__ == "__main__":
    asyncio.run(main())