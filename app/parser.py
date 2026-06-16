# app/parser.py
import httpx
import re
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def get_product_info(url: str):
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # ВНИМАНИЕ: Логика поиска цены зависит от конкретного сайта.
            # Для примера попробуем найти стандартные теги заголовка
            title = soup.find("h1").text.strip() if soup.find("h1") else "Товар без названия"
            
            # Это заглушка. Позже мы сделаем селекторы под конкретные магазины.
            price = 1000.0 
            
            return {"title": title, "price": price}
        except Exception as e:
            print(f"Ошибка парсинга: {e}")
            return None

def parse_price(html_content: str) -> float | None:
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ищем элемент по его уникальному ID
    price_element = soup.find(id="productMainPrice")
    
    if price_element:
        # Извлекаем текст: "         81600         "
        price_text = price_element.get_text()
        
        # Очищаем от лишних пробелов, переносов строк и символов валют
        # Оставим только цифры
        cleaned_price = re.sub(r'[^\d]', '', price_text)
        
        if cleaned_price:
            return float(cleaned_price)
    
    return None