import asyncio
from crawling.base import BaseCrawler, Product


class FarfetchCrawler(BaseCrawler):

    MEN_CLOTHING_URL = "https://www.farfetch.com/kr/shopping/men/clothing-2/items.aspx"

    async def get_products(self, url: str) -> list[Product]:

        page = await self._create_page()
        await page.goto(url)
        await page.wait_for_timeout(3000)

        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(1000)

        products = []

        items = await page.query_selector_all('[data-testid="productCard"]')

        for item in items:
            try:
                # 브랜드명
                brand_elem = await item.query_selector('[data-component="ProductCardBrandName"]')
                brand = await brand_elem.inner_text() if brand_elem else "Unknown"

                # 상품명
                name_elem = await item.query_selector('[data-component="ProductCardDescription"]')
                name = await name_elem.inner_text() if name_elem else "Unknown"

                # 가격
                price_elem = await item.query_selector('[data-component="PriceBrief"]')
                price = await price_elem.inner_text() if price_elem else "Unknown"

                # URL
                link_elem = await item.query_selector('a')
                href = await link_elem.get_attribute('href') if link_elem else ""
                product_url = f"https://www.farfetch.com{href}" if href else ""

                product = Product(
                    name=name.strip(),
                    brand=brand.strip(),
                    price=price.strip(),
                    url=product_url
                )
                products.append(product)

            except Exception as e:
                print(f"크롤링 에러: {e}")
                continue

        await page.close()
        return products

async def main():
    async with FarfetchCrawler(headless=False) as crawler:
        products = await crawler.get_products(FarfetchCrawler.MEN_CLOTHING_URL)

        print(f"\n총 {len(products)}개 상품 크롤링 완료\n")
        for i, p in enumerate(products[:10], 1): 
            print(f"{i}. {p.brand} - {p.name}")
            print(f"   가격: {p.price}")
            print(f"   URL: {p.url}")
            print()

if __name__ == "__main__":
    asyncio.run(main())