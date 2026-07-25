
import re
from bs4 import BeautifulSoup

from config import STORE_CONFIGS
from utils import build_url, clean_text, extract_sku_from_url, normalize_price, now_str


def parse_products(html: str, store_key: str, category: str, subcategory: str | None, source_url: str) -> list[dict]:
    store_config = STORE_CONFIGS[store_key]

    if store_key == "soriana":
        return parse_soriana_products(
            html=html,
            store_config=store_config,
            category=category,
            subcategory=subcategory,
            source_url=source_url,
        )

    if store_key == "chedraui":
        return parse_chedraui_products(
            html=html,
            store_config=store_config,
            category=category,
            subcategory=subcategory,
            source_url=source_url,
        )

    if store_key == "walmart":
        return parse_walmart_products(
            html=html,
            store_config=store_config,
            category=category,
            subcategory=subcategory,
            source_url=source_url,
        )

    raise NotImplementedError(f"No existe parser para la tienda: {store_key}")

def parse_soriana_products(
    html: str,
    store_config: dict,
    category: str,
    subcategory: str | None,
    source_url: str,
) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    selectors = store_config["selectors"]
    base_url = store_config["base_url"]
    products = []

    for link in soup.select(selectors["product_links"]):
        name = clean_text(link.get_text(" "))
        href = link.get("href")
        product_url = build_url(base_url, href)

        sku = (
            link.get(selectors["sku_attribute"])
            or extract_sku_from_url(product_url, store_config["sku_regex_patterns"])
        )

        price_scope = find_price_scope(
            start_node=link,
            price_selectors=[selectors["price_discount"], selectors["price_normal"]],
            max_levels=8,
        )

        price_discount = None
        price_normal = None

        if price_scope:
            discount_node = price_scope.select_one(selectors["price_discount"])
            normal_node = price_scope.select_one(selectors["price_normal"])

            if discount_node:
                price_discount = normalize_price(discount_node.get("value"))

            if normal_node:
                price_normal = normalize_price(normal_node.get("value"))

        if not name and not product_url:
            continue

        products.append(
            {
                "fecha_scraping": now_str(),
                "tienda": store_config["store_name"],
                "categoria": category,
                "subcategoria": subcategory,
                "nombre_producto": name,
                "sku": sku,
                "precio_normal": price_normal,
                "precio_descuento": price_discount,
                "url_producto": product_url,
                "url_origen": source_url,
            }
        )

    return products

def parse_chedraui_products(
    html: str,
    store_config: dict,
    category: str,
    subcategory: str | None,
    source_url: str,
) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    selectors = store_config["selectors"]
    base_url = store_config["base_url"]
    products = []
    seen_urls = set()

    for link in soup.select(selectors["product_links"]):
        href = link.get("href")
        product_url = build_url(base_url, href)

        if not product_url:
            continue

        if product_url in seen_urls:
            continue

        seen_urls.add(product_url)

        name = clean_text(link.get("aria-label"))

        if not name:
            name_node = link.select_one(selectors["product_name"])
            if name_node:
                name = clean_text(name_node.get_text(" "))

        sku = extract_sku_from_url(product_url, store_config["sku_regex_patterns"])

        price_scope = find_price_scope(
            start_node=link,
            price_selectors=[selectors["price_discount"], selectors["price_normal"]],
            max_levels=6,
        )

        price_discount = None
        price_normal = None

        if price_scope:
            discount_node = price_scope.select_one(selectors["price_discount"])
            normal_node = price_scope.select_one(selectors["price_normal"])

            if discount_node:
                price_discount = normalize_price(discount_node.get_text(" "))

            if normal_node:
                price_normal = normalize_price(normal_node.get_text(" "))

        if not name and not sku:
            continue

        products.append(
            {
                "fecha_scraping": now_str(),
                "tienda": store_config["store_name"],
                "categoria": category,
                "subcategoria": subcategory,
                "nombre_producto": name,
                "sku": sku,
                "precio_normal": price_normal,
                "precio_descuento": price_discount,
                "url_producto": product_url,
                "url_origen": source_url,
            }
        )

    return products

def parse_walmart_products(
    html: str,
    store_config: dict,
    category: str,
    subcategory: str | None,
    source_url: str,
) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    selectors = store_config["selectors"]
    base_url = store_config["base_url"]

    products = []
    seen_urls = set()

    for link in soup.select(selectors["product_links"]):
        href = link.get("href")
        product_url = build_url(base_url, href)

        if not product_url:
            continue

        if product_url in seen_urls:
            continue

        seen_urls.add(product_url)

        sku = (
            link.get(selectors["sku_attribute"])
            or extract_sku_from_url(product_url, store_config["sku_regex_patterns"])
        )

        price_scope = find_price_scope(
            start_node=link,
            price_selectors=[selectors["product_price"]],
            max_levels=10,
        )

        name = None
        price_discount = None
        price_normal = None

        if price_scope:
            title_node = price_scope.select_one(selectors["product_title"])

            if title_node:
                name = clean_text(title_node.get_text(" "))

            price_node = price_scope.select_one(selectors["product_price"])

            if price_node:
                price_discount, price_normal = extract_walmart_prices(
                    price_node=price_node,
                    old_price_selector=selectors.get("price_old"),
                )

        if not name:
            name = clean_text(link.get_text(" "))

        if not sku:
            sku = extract_sku_from_url(product_url, store_config["sku_regex_patterns"])

        if not name and not sku:
            continue

        products.append(
            {
                "fecha_scraping": now_str(),
                "tienda": store_config["store_name"],
                "categoria": category,
                "subcategoria": subcategory,
                "nombre_producto": name,
                "sku": sku,
                "precio_normal": price_normal,
                "precio_descuento": price_discount,
                "url_producto": product_url,
                "url_origen": source_url,
            }
        )

    return products

def extract_walmart_prices(price_node, old_price_selector: str | None = None) -> tuple[str | None, str | None]:
    text = clean_text(price_node.get_text(" ")) or ""

    current_price = None
    old_price = None

    current_match = re.search(
        r"precio\s+actual\s*\$?\s*([\d,]+(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    old_match = re.search(
        r"Antes\s*\$?\s*([\d,]+(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if current_match:
        current_price = normalize_price(current_match.group(1))

    if old_match:
        old_price = normalize_price(old_match.group(1))

    if not current_price:
        all_prices = re.findall(r"\$?\s*([\d,]+(?:\.\d+)?)", text)

        if all_prices:
            current_price = normalize_price(all_prices[0])

    if not old_price and old_price_selector:
        old_node = price_node.select_one(old_price_selector)

        if old_node:
            old_price = normalize_price(old_node.get_text(" "))

    return current_price, old_price

def find_price_scope(start_node, price_selectors: list[str], max_levels: int = 8):
    current = start_node

    for _ in range(max_levels):
        if current is None:
            return None

        if any(current.select_one(selector) for selector in price_selectors):
            return current

        current = current.parent

    return None