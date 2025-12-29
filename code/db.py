from config import supabase
from crawling.base import ProductItem


def save_products(items: list[ProductItem], source: str = "") -> dict:
    """크롤링 데이터 Supabase에 저장

    Args:
        items: ProductItem 리스트
        source: 크롤링 출처 (farfetch, zara 등)

    Returns:
        Supabase 응답
    """
    if not items:
        return {"data": [], "count": 0}

    data = [
        {
            "brand": item.brand,
            "name": item.name,
            "size": item.size,
            "price": item.price,
            "note": item.note,
            "url": item.url,
            "source": source,
        }
        for item in items
    ]

    return supabase.table("products").insert(data).execute()
