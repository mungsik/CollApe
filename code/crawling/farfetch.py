import asyncio
import random
import re
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
        await page.wait_for_timeout(random_delay(2000, 4000))

        # 언어를 영어로 설정
        try:
            lang_btn = await page.query_selector('[aria-label="Language and region"]')
            if lang_btn:
                await lang_btn.click()
                await page.wait_for_timeout(random_delay(800, 1500))
                eng_btn = await page.query_selector('[data-testid="btn-English (American)"]')
                if eng_btn:
                    await eng_btn.click()
                    await page.wait_for_timeout(random_delay(1500, 2500))
        except Exception as e:
            print(f"언어 설정 실패 : {e}")

        # 페이지 끝까지 스크롤
        await self.scroll_page(page)

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

                # URL이 없으면 스킵 
                if not product_url:
                    continue

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
        await page.wait_for_timeout(random_delay(2500, 5000))

        size_prices = []

        # 이미지 URL 수집
        images = []
        img_elems = await page.query_selector_all('[data-component="Img"]')
        for img_elem in img_elems:
            src = await img_elem.get_attribute('src')
            if src and 'farfetch-contents.com' in src:
                images.append(src)

        dropdown = await page.query_selector('[data-component="SizeSelectorLabel"]')

        if not dropdown:
            await page.close()
            return {"size_prices": [], "images": images}

        await dropdown.click()
        await page.wait_for_selector('[data-component="SizeSelectorOption"]', timeout=5000)
        await page.wait_for_timeout(random_delay(800, 1500))

        options = await page.query_selector_all('[data-component="SizeSelectorOption"]')
        option_count = len(options)

        for i in range(option_count):
            # 드롭다운 열기
            if i > 0:
                dropdown = await page.query_selector('[data-component="SizeSelectorLabel"]')
                await dropdown.click()
                await page.wait_for_selector('[data-component="SizeSelectorOption"]', timeout=5000)
                await page.wait_for_timeout(random_delay(800, 1500))
                options = await page.query_selector_all('[data-component="SizeSelectorOption"]')

            option = options[i]

            size_elem = await option.query_selector('[data-component="SizeSelectorOptionSize"]')
            size = await size_elem.inner_text() if size_elem else "Unknown"

            # 비고 가져오기
            notes = []
            label_elem = await option.query_selector('[data-component="SizeSelectorOptionLabel"]')
            if label_elem:
                label_text = await label_elem.inner_text()
                if label_text.strip():
                    notes.append(label_text.strip().replace('\xa0', ' '))

            # 클릭 전 가격 저장 (변경 감지용)
            old_price_elem = await page.query_selector('[data-component="PriceCallout"] [data-component="PriceFinal"]')
            if not old_price_elem:
                old_price_elem = await page.query_selector('[data-component="PriceCallout"] [data-component="Body"]')
            old_price = await old_price_elem.inner_text() if old_price_elem else ""

            # 사이즈 클릭
            await option.click()
            await page.wait_for_timeout(random_delay(1000, 2500))

            # 가격이 변경될 때까지 대기 (최대 3초)
            for _ in range(6):
                price_elem = await page.query_selector('[data-component="PriceCallout"] [data-component="PriceFinal"]')
                if not price_elem:
                    price_elem = await page.query_selector('[data-component="PriceCallout"] [data-component="Body"]')
                new_price = await price_elem.inner_text() if price_elem else ""
                if new_price != old_price:
                    break
                await page.wait_for_timeout(500)

            # 상단에서 최종가격 가져오기 (할인가 우선, 없으면 정가)
            price_elem = await page.query_selector('[data-component="PriceCallout"] [data-component="PriceFinal"]')
            if not price_elem:
                price_elem = await page.query_selector('[data-component="PriceCallout"] [data-component="Body"]')

            if price_elem:
                price = await price_elem.inner_text()
                price = price.strip().replace('\xa0', ' ')
            else:
                price = "Unknown"

            # 상단에서 비고 가져오기 (가격 제외)
            footnote_elems = await page.query_selector_all('[data-component="PriceCallout"] [data-component="Footnote"]')
            for footnote_elem in footnote_elems:
                footnote = await footnote_elem.inner_text()
                footnote = footnote.strip().replace('\xa0', ' ')
                # 가격 패턴 제외 (₩, $, %, 숫자만 있는 경우 등)
                if footnote and not re.match(r'^[\d₩$€£%,.\-\s]+$', footnote):
                    notes.append(footnote)

            note = ", ".join(notes)

            size_prices.append({
                "size": size.strip().replace('\xa0', ' '),
                "price": price,
                "note": note
            })

        await page.close()
        return {"size_prices": size_prices, "images": images}

    async def crawl_all(self, list_url: str, limit: int = 20) -> list[ProductItem]:
        """상세 페이지 크롤링"""
        results = []

        print("목록 페이지 크롤링 중...")
        products = await self.get_product_urls(list_url)
        print(f"{len(products)}개 상품 발견 (최대 {limit}개 크롤링)\n")

        products = products[:limit]

        for i, product in enumerate(products, 1):
            print(f"[{i}/{len(products)}] {product['brand']} - {product['name']}")

            try:
                result = await self.get_product_price_by_size(product['url'])
                size_prices = result["size_prices"]
                images = result["images"]

                for sp in size_prices:
                    item = ProductItem(
                        brand=product['brand'],
                        name=product['name'],
                        size=sp['size'],
                        price=sp['price'],
                        note=sp['note'],
                        url=product['url'],
                        images=images
                    )
                    results.append(item)

            except Exception as e:
                print(f"crawling error: {e}")
                continue

            # 상품 간 랜덤 딜레이. 봇 차단 방지
            if random.random() < 0.2:
                delay = random_delay(8000, 15000)
            else:
                delay = random_delay(3000, 6000)
            await asyncio.sleep(delay / 1000)

        return results

async def main(url: str):
    async with FarfetchCrawler(headless=False) as crawler:
        items = await crawler.crawl_all(url)

        print(f"\n총 {len(items)}개 데이터 크롤링 완료\n")

        for item in items[:2]:
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