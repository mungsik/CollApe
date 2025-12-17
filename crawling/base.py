from abc import ABC, abstractmethod
from dataclasses import dataclass
from playwright.async_api import async_playwright


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