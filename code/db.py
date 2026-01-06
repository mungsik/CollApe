from config import supabase
from crawling.base import ProductItem


def save_products(items: list[ProductItem], source: str = "") -> dict:
    """크롤링 데이터 Supabase에 저장"""
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
            "farfetch_images": item.images,
        }
        for item in items
    ]

    return supabase.table("products").insert(data).execute()
