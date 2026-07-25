from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "output"
HTML_DEBUG_DIR = DATA_DIR / "html_debug"

OUTPUT_COLUMNS = [
    "fecha_scraping",
    "tienda",
    "categoria",
    "subcategoria",
    "nombre_producto",
    "sku",
    "precio_normal",
    "precio_descuento",
    "url_producto",
]

SUMMARY_COLUMNS = [
    "date",
    "store",
    "category",
    "subcategory_count",
    "products_found",
    "products_saved",
    "errors",
    "duration_seconds",
]

BROWSER_CONFIG = {
    "headless": False,
    "timeout_ms": 60000,
    "wait_until": "networkidle",
    "locale": "es-MX",
    "viewport": {"width": 1366, "height": 768},
}

SCRAPER_CONFIG = {
    "pause_min_seconds": 1.5,
    "pause_max_seconds": 3.5,
    "scroll_steps": 6,
    "scroll_pause_seconds": 0.8,
}

STORE_CONFIGS = {
    "soriana": {
        "store_name": "Soriana",
        "base_url": "https://www.soriana.com",
        "output_filename": "soriana_productos.csv",
        "navigation_type": "two_level_refinements",
        "categories": [
            {
                "name": "frutas-y-verduras",
                "url": "https://www.soriana.com/frutas-y-verduras/",
            },
            {
                "name": "lacteos-y-huevo",
                "url": "https://www.soriana.com/lacteos-y-huevo/",
            },
            {
                "name": "carnes-pescados-y-mariscos",
                "url": "https://www.soriana.com/carnes-pescados-y-mariscos/",
            },
        ],
        "selectors": {
            "refinement_buttons": "button.btn-refinement",
            "refinement_url_attribute": "data-href",
            "product_links": "a.product-tile--link",
            "sku_attribute": "link-identifier",
            "price_discount": 'input[name="clevertap-price"]',
            "price_normal": 'input[name="clevertap-list-price"]',
        },
        "sku_regex_patterns": [
            r"/(\d+)\.html",
        ],
    },
    "chedraui": {
        "store_name": "Chedraui",
        "base_url": "https://www.chedraui.com.mx",
        "navigation_type": "paginated_categories",
        "max_pages": 80,

        "goto_wait_until": "domcontentloaded",
        "timeout_ms": 45000,
        "goto_retries": 3,
        "stop_after_empty_pages": 1,

        "categories": [
            {
                "name": "carnes-pescados-y-mariscos",
                "url": "https://www.chedraui.com.mx/supermercado/carnes-pescados-y-mariscos",
            },
            {
                "name": "frutas-y-verduras",
                "url": "https://www.chedraui.com.mx/supermercado/frutas-y-verduras",
            },
            {
                "name": "lacteos-y-huevo",
                "url": "https://www.chedraui.com.mx/supermercado/lacteos-y-huevo",
            },
        ],
        "selectors": {
            "product_links": "a.vtex-product-summary-2-x-clearLink",
            "product_name": ".vtex-product-summary-2-x-nameContainer h3",
            "price_discount": "span.chedrauimx-products-simulator-0-x-simulatedSellingPrice",
            "price_normal": "span.chedrauimx-products-simulator-0-x-simulatedListPrice",
            "next_page": 'a[aria-label="Next page"]',
        },
        "sku_regex_patterns": [
            r"-(\d+)/p(?:$|\?)",
            r"/(\d+)/p(?:$|\?)",
        ],
    },
        "walmart": {
        "store_name": "Walmart",
        "base_url": "https://www.walmart.com.mx",
        "navigation_type": "two_level_links_and_chips",

        "goto_wait_until": "domcontentloaded",
        "timeout_ms": 60000,
        "goto_retries": 3,
        "product_wait_timeout_ms": 20000,

        "categories": [
            {
                "name": "carnes-pescados-y-mariscos",
                "url": "https://www.walmart.com.mx/content/carnes-pescados-y-mariscos/120008",
            },
            {
                "name": "lacteos",
                "url": "https://www.walmart.com.mx/content/lacteos/120006",
            },
            {
                "name": "frutas-y-verduras",
                "url": "https://www.walmart.com.mx/content/frutas-y-verduras/120007",
            },
        ],

        "selectors": {
            "primary_links": 'a[role="link"][href^="/content/"]',
            "primary_link_url_attribute": "href",

            "secondary_chips": 'button[role="link"][aria-label][class*="Chip_chip"]',
            "secondary_chip_name_attribute": "aria-label",

            "product_links": 'a[link-identifier][href*="/ip/"]',
            "sku_attribute": "link-identifier",

            "product_title": 'span[data-automation-id="product-title"]',
            "product_price": 'div[data-automation-id="product-price"]',
            "price_old": "span.strike",
        },

        "sku_regex_patterns": [
            r"/ip/[^/]+/(\d+)(?:\?|$)",
            r"/(\d+)(?:\?|$)",
        ],
    },
}