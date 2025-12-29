import asyncio
import sys
from crawling.base import BaseCrawler, ProductItem
from crawling.utils import random_delay
from db import save_products

'''
windows 콘솔 기본 인코딩 = cp949
원화 기호나 특수 공백 같은 유니코드 문자를 출력할 수 없어서 추가
print문 확인할 때만 필요.
'''
sys.stdout.reconfigure(encoding='utf-8')

class FarfetchCrawler(BaseCrawler):

    async def get_product_urls(self, url: str) -> list[dict]:
        """목록 페이지에서 상품 URL, 브랜드명, 제품명 가져오기"""
        page = await self._create_page()
        await page.goto(url)
        await page.wait_for_selector('[data-testid="productCard"]', timeout=10000)
        await page.wait_for_timeout(random_delay(1000, 2000))

        # 페이지 끝까지 스크롤
        prev_height = 0
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(random_delay(1500, 2500))
            curr_height = await page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                break
            prev_height = curr_height

        products = []
        items = await page.query_selector_all('[data-testid="productCard"]')

        for item in items:
            try:
                brand_elem = await item.query_selector('[data-component="ProductCardBrandName"]')
                brand = await brand_elem.inner_text() if brand_elem else "Unknown"

                name_elem = await item.query_selector('[data-component="ProductCardDescription"]')
                name = await name_elem.inner_text() if name_elem else "Unknown"

                link_elem = await item.query_selector('a')
                href = await link_elem.get_attribute('href') if link_elem else ""
                product_url = f"https://www.farfetch.com{href}" if href else ""

                products.append({
                    "brand": brand.strip(),
                    "name": name.strip(),
                    "url": product_url
                })

            except Exception as e:
                print(f"목록 크롤링 에러: {e}")
                continue

        await page.close()
        return products

    async def get_product_price_by_size(self, product_url: str) -> list[dict]:
        """상세 페이지에서 사이즈별 가격, 비고 가져오기"""
        page = await self._create_page()
        await page.goto(product_url)
        await page.wait_for_selector('[data-component="SizeSelectorLabel"]', timeout=10000)
        await page.wait_for_timeout(random_delay(1000, 2000))

        size_prices = []

        # 기본 가격
        base_price_elem = await page.query_selector('p[data-component="Body"].ltr-137vk2a-Body')
        base_price = await base_price_elem.inner_text() if base_price_elem else "Unknown"
        base_price = base_price.strip().replace('\xa0', ' ')

        # 비고
        base_footnote_elem = await page.query_selector('[data-component="PriceCallout"] [data-component="Footnote"]')
        base_footnote = ""
        if base_footnote_elem:
            base_footnote = await base_footnote_elem.inner_text()
            base_footnote = base_footnote.strip().replace('\xa0', ' ')

        dropdown = await page.query_selector('[data-component="SizeSelectorLabel"]')

        if not dropdown:
            await page.close()
            return []

        await dropdown.click()
        await page.wait_for_selector('[data-component="SizeSelectorOption"]', timeout=5000)
        await page.wait_for_timeout(random_delay(300, 700))

        options = await page.query_selector_all('[data-component="SizeSelectorOption"]')

        for option in options:
            size_elem = await option.query_selector('[data-component="SizeSelectorOptionSize"]')
            size = await size_elem.inner_text() if size_elem else "Unknown"

            # 사이즈별 가격 (없으면 기본 가격)
            price_elem = await option.query_selector('[data-component="DropdownOptionWrapper"]')
            if price_elem:
                price = await price_elem.inner_text()
                price = price.strip().replace('\xa0', ' ')
            if not price_elem or not price:
                price = base_price

            # 비고
            notes = []
            label_elem = await option.query_selector('[data-component="SizeSelectorOptionLabel"]')
            if label_elem:
                label_text = await label_elem.inner_text()
                if label_text.strip():
                    notes.append(label_text.strip().replace('\xa0', ' '))

            if base_footnote:
                notes.append(base_footnote)

            note = ", ".join(notes)

            size_prices.append({
                "size": size.strip().replace('\xa0', ' '),
                "price": price,
                "note": note
            })

        await page.close()
        return size_prices

    async def crawl_all(self, list_url: str) -> list[ProductItem]:
        """목록 → 상세 페이지 크롤링하여 DB 적재용 데이터 반환"""
        results = []

        # 1. 목록에서 상품 URL 가져오기
        print("목록 페이지 크롤링 중...")
        products = await self.get_product_urls(list_url)
        print(f"{len(products)}개 상품 발견\n")

        # 2. 각 상품 상세 페이지 크롤링
        for i, product in enumerate(products, 1):
            print(f"[{i}/{len(products)}] {product['brand']} - {product['name']}")

            try:
                size_prices = await self.get_product_price_by_size(product['url'])

                for sp in size_prices:
                    item = ProductItem(
                        brand=product['brand'],
                        name=product['name'],
                        size=sp['size'],
                        price=sp['price'],
                        note=sp['note'],
                        url=product['url']
                    )
                    results.append(item)

            except Exception as e:
                print(f"crawling error: {e}")
                continue

        return results

async def main(url: str):
    async with FarfetchCrawler(headless=False) as crawler:
        items = await crawler.crawl_all(url)

        print(f"\n총 {len(items)}개 데이터 크롤링 완료\n")

        for item in items[:10]:
            note = f" ({item.note})" if item.note else ""
            print(f"{item.brand} | {item.name} | {item.size} | {item.price}{note}")

        if items:
            try:
                result = save_products(items, source="farfetch")
                print(f"\nSupabase 저장 완료: {len(result.data)}개")
            except Exception as e:
                print(f"\nSupabase 저장 실패: {e}")

if __name__ == "__main__":
    target_url = "https://www.farfetch.com/kr/shopping/men/clothing-2/items.aspx"
    asyncio.run(main(target_url))