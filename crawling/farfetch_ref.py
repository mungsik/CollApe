import asyncio
from crawling.base import BaseCrawler, Product


class FarfetchCrawler(BaseCrawler):
    """Farfetch 사이트 크롤러"""

    BASE_URL = "https://www.farfetch.com"

    # Farfetch 전용 셀렉터
    SELECTORS = {
        "product_card": '[data-testid="productCard"]',
        "card_brand": '[data-testid="productCard-brand"]',
        "card_name": '[data-testid="productCard-description"]',
        "card_price": '[data-testid="price"]',
        "detail_brand": '[data-testid="product-brand"]',
        "detail_name": '[data-testid="product-name"]',
        "detail_price": '[data-testid="price"]',
        "detail_image": '[data-testid="product-image"] img',
    }

    async def search_products(self, query: str, max_items: int = 20) -> list[Product]:
        """검색어로 상품을 검색합니다."""
        page = await self._create_page()
        products = []

        try:
            search_url = f"{self.BASE_URL}/kr/shopping/women/search/items.aspx?q={query}"
            await page.goto(search_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            await page.wait_for_selector(self.SELECTORS["product_card"], timeout=10000)
            await self._scroll_page(page)

            product_cards = await page.query_selector_all(self.SELECTORS["product_card"])

            for card in product_cards[:max_items]:
                product = await self._parse_product_card(card)
                if product:
                    products.append(product)

        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
        finally:
            await page.close()

        return products

    async def get_category_products(
        self, category_url: str, max_items: int = 20
    ) -> list[Product]:
        """카테고리 페이지에서 상품을 가져옵니다."""
        page = await self._create_page()
        products = []

        try:
            await page.goto(category_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            await page.wait_for_selector(self.SELECTORS["product_card"], timeout=10000)
            await self._scroll_page(page)

            product_cards = await page.query_selector_all(self.SELECTORS["product_card"])

            for card in product_cards[:max_items]:
                product = await self._parse_product_card(card)
                if product:
                    products.append(product)

        except Exception as e:
            print(f"카테고리 크롤링 중 오류 발생: {e}")
        finally:
            await page.close()

        return products

    async def get_product_detail(self, product_url: str) -> Product | None:
        """상품 상세 페이지에서 정보를 가져옵니다."""
        page = await self._create_page()

        try:
            await page.goto(product_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            brand = await self._safe_get_text(page, self.SELECTORS["detail_brand"])
            name = await self._safe_get_text(page, self.SELECTORS["detail_name"])
            price = await self._safe_get_text(page, self.SELECTORS["detail_price"])
            image_url = await self._safe_get_attribute(page, self.SELECTORS["detail_image"], "src")

            return Product(
                name=name,
                brand=brand,
                price=price,
                url=product_url,
                image_url=image_url,
            )

        except Exception as e:
            print(f"상품 상세 크롤링 중 오류 발생: {e}")
            return None
        finally:
            await page.close()

    async def _parse_product_card(self, card) -> Product | None:
        """상품 카드에서 정보를 파싱합니다."""
        try:
            # 링크
            href = await self._safe_get_attribute(card, "a", "href")
            url = f"{self.BASE_URL}{href}" if href and not href.startswith("http") else href

            # 상품 정보
            brand = await self._safe_get_text(card, self.SELECTORS["card_brand"])
            name = await self._safe_get_text(card, self.SELECTORS["card_name"])
            price = await self._safe_get_text(card, self.SELECTORS["card_price"])
            image_url = await self._safe_get_attribute(card, "img", "src")

            return Product(
                name=name,
                brand=brand,
                price=price,
                url=url or "",
                image_url=image_url,
            )

        except Exception as e:
            print(f"상품 카드 파싱 중 오류: {e}")
            return None


async def main():
    async with FarfetchCrawler(headless=False) as crawler:
        products = await crawler.search_products("gucci bag", max_items=10)

        print(f"\n총 {len(products)}개의 상품을 찾았습니다.\n")

        for i, product in enumerate(products, 1):
            print(f"[{i}] {product.brand} - {product.name}")
            print(f"    가격: {product.price}")
            print(f"    URL: {product.url}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
