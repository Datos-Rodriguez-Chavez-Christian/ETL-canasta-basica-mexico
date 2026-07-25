import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from config import BROWSER_CONFIG, SCRAPER_CONFIG, STORE_CONFIGS
from parser import parse_products
from utils import build_url, clean_text, now_str, random_pause, save_html_debug


class ProductScraper:
    def __init__(self, store_key: str, headless: bool | None = None):
        if store_key not in STORE_CONFIGS:
            raise ValueError(f"Tienda no configurada: {store_key}")

        self.store_key = store_key
        self.store_config = STORE_CONFIGS[store_key]
        self.browser_config = BROWSER_CONFIG.copy()

        if headless is not None:
            self.browser_config["headless"] = headless

        self.summary_rows = []

    def run(self, limit_level_1: int | None = None, limit_level_2: int | None = None) -> tuple[list[dict], list[dict]]:
        navigation_type = self.store_config["navigation_type"]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.browser_config["headless"])
            context = browser.new_context(
                locale=self.browser_config["locale"],
                viewport=self.browser_config["viewport"],
            )
            page = context.new_page()

            if navigation_type == "two_level_refinements":
                products = self._run_two_level_refinements(page, limit_level_1, limit_level_2)

            elif navigation_type == "paginated_categories":
                products = self._run_paginated_categories(page)

            elif navigation_type == "two_level_links_and_chips":
                products = self._run_two_level_links_and_chips(page, limit_level_1, limit_level_2)

            else:
                browser.close()
                raise NotImplementedError(f"Tipo de navegación no implementado: {navigation_type}")

            browser.close()

        return products, self.summary_rows
    
    def _run_two_level_refinements(
        self,
        page,
        limit_level_1: int | None,
        limit_level_2: int | None,
    ) -> list[dict]:
        all_products = []

        for category_config in self.store_config["categories"]:
            category_start = time.time()
            errors = 0
            category_products = []
            subcategory_count = 0
            category_name = category_config["name"]
            category_url = category_config["url"]

            print("\n" + "=" * 80)
            print(f"[{self.store_config['store_name']}] Categoría principal: {category_name}")
            print(category_url)

            try:
                self._goto(page, category_url)
                level_1_items = self._extract_refinements(page)
                level_1_items = self._apply_limit(level_1_items, limit_level_1)

                print(f"Refinamientos nivel 1 encontrados: {len(level_1_items)}")

                for level_1 in level_1_items:
                    print("-" * 80)
                    print(f"Nivel 1: {level_1['name']}")
                    print(level_1["url"])

                    self._goto(page, level_1["url"])
                    level_2_items = self._extract_refinements(page)
                    level_2_items = self._remove_duplicate_refinements(level_2_items)
                    level_2_items = self._apply_limit(level_2_items, limit_level_2)

                    if level_2_items:
                        print(f"Refinamientos nivel 2 encontrados: {len(level_2_items)}")
                        targets = level_2_items
                    else:
                        print("Sin nivel 2; se extraen productos desde nivel 1.")
                        targets = [level_1]

                    for target in targets:
                        subcategory_count += 1
                        subcategory_name = target["name"]

                        print(f"Subcategoría/productos: {subcategory_name}")
                        print(target["url"])

                        try:
                            self._goto(page, target["url"])
                            self._scroll_full(page)
                            html = page.content()

                            products = parse_products(
                                html=html,
                                store_key=self.store_key,
                                category=category_name,
                                subcategory=subcategory_name,
                                source_url=page.url,
                            )

                            print(f"Productos encontrados: {len(products)}")

                            if not products:
                                debug_path = save_html_debug(
                                    store_key=self.store_key,
                                    category=category_name,
                                    subcategory=subcategory_name,
                                    html=html,
                                    reason="sin_productos",
                                )
                                print(f"HTML debug guardado: {debug_path}")

                            category_products.extend(products)
                            all_products.extend(products)

                        except Exception as exc:
                            errors += 1
                            print(f"ERROR en subcategoría {subcategory_name}: {exc}")

            except Exception as exc:
                errors += 1
                print(f"ERROR en categoría {category_name}: {exc}")

            duration = round(time.time() - category_start, 2)

            self.summary_rows.append(
                {
                    "date": now_str(),
                    "store": self.store_config["store_name"],
                    "category": category_name,
                    "subcategory_count": subcategory_count,
                    "products_found": len(category_products),
                    "products_saved": len(category_products),
                    "errors": errors,
                    "duration_seconds": duration,
                }
            )

        return all_products

    def _run_paginated_categories(self, page) -> list[dict]:
        all_products = []

        max_pages = self.store_config.get("max_pages")

        for category_config in self.store_config["categories"]:
            category_start = time.time()
            errors = 0
            category_products = []
            pages_processed = 0
            empty_pages = 0
            stop_after_empty_pages = self.store_config.get("stop_after_empty_pages", 1)

            category_name = category_config["name"]
            current_url = category_config["url"]
            visited_urls = set()
            page_number = 1

            print("\n" + "=" * 80)
            print(f"[{self.store_config['store_name']}] Categoría paginada: {category_name}")
            print(current_url)

            while current_url:
                if current_url in visited_urls:
                    print(f"URL repetida detectada. Se detiene paginación: {current_url}")
                    break

                if max_pages is not None and page_number > max_pages:
                    print(f"Límite de páginas alcanzado para {category_name}: {max_pages}")
                    break

                visited_urls.add(current_url)

                print("-" * 80)
                print(f"Página {page_number}: {current_url}")

                try:
                    self._goto(page, current_url)
                    self._wait_for_product_links(page)
                    self._scroll_full(page)
                    self._wait_for_product_links(page)

                    html = page.content()
                    pages_processed += 1

                    products = parse_products(
                        html=html,
                        store_key=self.store_key,
                        category=category_name,
                        subcategory=None,
                        source_url=page.url,
                    )

                    print(f"Productos encontrados en página {page_number}: {len(products)}")

                    if not products:
                        empty_pages += 1

                        debug_path = save_html_debug(
                            store_key=self.store_key,
                            category=category_name,
                            subcategory=f"pagina_{page_number}",
                            html=html,
                            reason="sin_productos",
                        )
                        print(f"HTML debug guardado: {debug_path}")

                        if empty_pages >= stop_after_empty_pages:
                            print(
                                f"Se encontraron {empty_pages} página(s) consecutiva(s) sin productos. "
                                f"Se termina la categoría: {category_name}"
                            )
                            break

                    else:
                        empty_pages = 0

                    category_products.extend(products)
                    all_products.extend(products)

                    next_url = self._extract_next_page_url(page)

                    if not next_url:
                        print("No se encontró página siguiente. Categoría terminada.")
                        break

                    current_url = next_url
                    page_number += 1

                except Exception as exc:
                    errors += 1
                    print(f"ERROR en categoría {category_name}, página {page_number}: {exc}")
                    break

            duration = round(time.time() - category_start, 2)

            self.summary_rows.append(
                {
                    "date": now_str(),
                    "store": self.store_config["store_name"],
                    "category": category_name,
                    "subcategory_count": pages_processed,
                    "products_found": len(category_products),
                    "products_saved": len(category_products),
                    "errors": errors,
                    "duration_seconds": duration,
                }
            )

        return all_products

    def _wait_for_product_links(self, page) -> None:
        selector = self.store_config["selectors"].get("product_links")

        if not selector:
            return

        timeout_ms = self.store_config.get("product_wait_timeout_ms", 15000)

        try:
            page.wait_for_selector(
                selector,
                timeout=timeout_ms,
            )
        except PlaywrightTimeoutError:
            print("Aviso: no aparecieron productos dentro del tiempo esperado. Se intentará parsear el HTML actual.")
            
    def _extract_next_page_url(self, page) -> str | None:
        selector = self.store_config["selectors"].get("next_page")

        if not selector:
            return None

        links = page.locator(selector)
        total = links.count()

        for i in range(total):
            link = links.nth(i)

            try:
                href = link.get_attribute("href", timeout=5000)
            except PlaywrightTimeoutError:
                continue

            next_url = build_url(self.store_config["base_url"], href)

            if next_url and next_url != page.url:
                return next_url

        return None

    def _run_two_level_links_and_chips(
        self,
        page,
        limit_level_1: int | None,
        limit_level_2: int | None,
    ) -> list[dict]:
        all_products = []

        for category_config in self.store_config["categories"]:
            category_start = time.time()
            errors = 0
            category_products = []
            targets_processed = 0

            category_name = category_config["name"]
            category_url = category_config["url"]

            print("\n" + "=" * 80)
            print(f"[{self.store_config['store_name']}] Categoría principal: {category_name}")
            print(category_url)

            try:
                self._goto(page, category_url)
                self._scroll_full(page)

                primary_links = self._extract_primary_links(page)
                primary_links = self._apply_limit(primary_links, limit_level_1)

                print(f"Botones principales encontrados: {len(primary_links)}")

                if not primary_links:
                    print("No se encontraron botones principales. Se intentará extraer productos desde la categoría principal.")

                    products = self._extract_products_from_current_page(
                        page=page,
                        category_name=category_name,
                        subcategory_name=None,
                    )

                    targets_processed += 1
                    category_products.extend(products)
                    all_products.extend(products)
                    continue

                for primary in primary_links:
                    print("-" * 80)
                    print(f"Botón principal: {primary['name']}")
                    print(primary["url"])

                    try:
                        self._goto(page, primary["url"])
                        self._scroll_full(page)

                        secondary_chips = self._extract_secondary_chips(page)
                        secondary_chips = self._apply_limit(secondary_chips, limit_level_2)

                        print(f"Chips secundarios encontrados: {len(secondary_chips)}")

                        if not secondary_chips:
                            subcategory_name = primary["name"]

                            products = self._extract_products_from_current_page(
                                page=page,
                                category_name=category_name,
                                subcategory_name=subcategory_name,
                            )

                            targets_processed += 1
                            category_products.extend(products)
                            all_products.extend(products)
                            continue

                        for chip in secondary_chips:
                            subcategory_name = f"{primary['name']} > {chip['name']}"

                            print(f"Chip secundario: {chip['name']}")

                            try:
                                self._goto(page, primary["url"])

                                clicked = self._click_secondary_chip(page, chip["name"])

                                if not clicked:
                                    errors += 1
                                    print(f"No se pudo hacer click en chip: {chip['name']}")
                                    continue

                                products = self._extract_products_from_current_page(
                                    page=page,
                                    category_name=category_name,
                                    subcategory_name=subcategory_name,
                                )

                                targets_processed += 1
                                category_products.extend(products)
                                all_products.extend(products)

                            except Exception as exc:
                                errors += 1
                                print(f"ERROR en chip {chip['name']}: {exc}")

                    except Exception as exc:
                        errors += 1
                        print(f"ERROR en botón principal {primary['name']}: {exc}")

            except Exception as exc:
                errors += 1
                print(f"ERROR en categoría {category_name}: {exc}")

            duration = round(time.time() - category_start, 2)

            self.summary_rows.append(
                {
                    "date": now_str(),
                    "store": self.store_config["store_name"],
                    "category": category_name,
                    "subcategory_count": targets_processed,
                    "products_found": len(category_products),
                    "products_saved": len(category_products),
                    "errors": errors,
                    "duration_seconds": duration,
                }
            )

        return all_products

    def _goto(self, page, url: str) -> None:
        wait_until = self.store_config.get(
            "goto_wait_until",
            self.browser_config["wait_until"],
        )

        timeout_ms = self.store_config.get(
            "timeout_ms",
            self.browser_config["timeout_ms"],
        )

        retries = self.store_config.get("goto_retries", 1)
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                page.goto(
                    url,
                    wait_until=wait_until,
                    timeout=timeout_ms,
                )

                random_pause(
                    SCRAPER_CONFIG["pause_min_seconds"],
                    SCRAPER_CONFIG["pause_max_seconds"],
                )

                return

            except (PlaywrightTimeoutError, PlaywrightError) as exc:
                last_error = exc
                print(f"Aviso: error navegando a {url}. Intento {attempt}/{retries}")
                print(f"Detalle: {exc}")

                if attempt < retries:
                    random_pause(3, 7)
                    continue

        raise last_error
    
    def _extract_refinements(self, page) -> list[dict]:
        selectors = self.store_config["selectors"]
        selector = selectors["refinement_buttons"]
        url_attribute = selectors["refinement_url_attribute"]
        base_url = self.store_config["base_url"]

        results = []
        buttons = page.locator(selector)
        total = buttons.count()

        for i in range(total):
            button = buttons.nth(i)

            try:
                name = clean_text(button.inner_text(timeout=5000))
                href = button.get_attribute(url_attribute, timeout=5000)
            except PlaywrightTimeoutError:
                continue

            url = build_url(base_url, href)

            if name and url:
                results.append(
                    {
                        "name": name,
                        "url": url,
                        "raw_url": href,
                    }
                )

        return self._remove_duplicate_refinements(results)

    def _extract_primary_links(self, page) -> list[dict]:
        selectors = self.store_config["selectors"]
        selector = selectors["primary_links"]
        url_attribute = selectors.get("primary_link_url_attribute", "href")
        base_url = self.store_config["base_url"]

        results = []
        links = page.locator(selector)
        total = links.count()

        for i in range(total):
            link = links.nth(i)

            try:
                name = clean_text(link.inner_text(timeout=5000))
                href = link.get_attribute(url_attribute, timeout=5000)
            except PlaywrightTimeoutError:
                continue

            url = build_url(base_url, href)

            if name and url:
                results.append(
                    {
                        "name": name,
                        "url": url,
                        "raw_url": href,
                    }
                )

        return self._remove_duplicate_refinements(results)

    def _extract_secondary_chips(self, page) -> list[dict]:
        selectors = self.store_config["selectors"]
        selector = selectors["secondary_chips"]
        name_attribute = selectors.get("secondary_chip_name_attribute", "aria-label")

        results = []
        chips = page.locator(selector)
        total = chips.count()

        for i in range(total):
            chip = chips.nth(i)

            try:
                name = clean_text(chip.get_attribute(name_attribute, timeout=5000))

                if not name:
                    name = clean_text(chip.inner_text(timeout=5000))

            except PlaywrightTimeoutError:
                continue

            if name:
                results.append({"name": name})

        return self._remove_duplicate_chip_names(results)

    def _click_secondary_chip(self, page, chip_name: str) -> bool:
        selectors = self.store_config["selectors"]
        selector = selectors["secondary_chips"]
        name_attribute = selectors.get("secondary_chip_name_attribute", "aria-label")

        chips = page.locator(selector)
        total = chips.count()

        for i in range(total):
            chip = chips.nth(i)

            try:
                current_name = clean_text(chip.get_attribute(name_attribute, timeout=5000))

                if not current_name:
                    current_name = clean_text(chip.inner_text(timeout=5000))

                if current_name != chip_name:
                    continue

                chip.scroll_into_view_if_needed(timeout=10000)
                chip.click(timeout=15000)

                try:
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                except PlaywrightTimeoutError:
                    pass

                random_pause(2, 4)
                return True

            except (PlaywrightTimeoutError, PlaywrightError):
                continue

        return False

    def _extract_products_from_current_page(
        self,
        page,
        category_name: str,
        subcategory_name: str | None,
    ) -> list[dict]:
        self._wait_for_product_links(page)
        self._scroll_full(page)
        self._wait_for_product_links(page)

        html = page.content()

        products = parse_products(
            html=html,
            store_key=self.store_key,
            category=category_name,
            subcategory=subcategory_name,
            source_url=page.url,
        )

        print(f"Productos encontrados: {len(products)}")

        if not products:
            debug_path = save_html_debug(
                store_key=self.store_key,
                category=category_name,
                subcategory=subcategory_name,
                html=html,
                reason="sin_productos",
            )
            print(f"HTML debug guardado: {debug_path}")

        return products

    @staticmethod
    def _remove_duplicate_chip_names(items: list[dict]) -> list[dict]:
        seen = set()
        unique_items = []

        for item in items:
            key = item["name"]

            if key in seen:
                continue

            seen.add(key)
            unique_items.append(item)

        return unique_items

    @staticmethod
    def _remove_duplicate_refinements(items: list[dict]) -> list[dict]:
        seen = set()
        unique_items = []

        for item in items:
            key = item["url"]
            if key in seen:
                continue

            seen.add(key)
            unique_items.append(item)

        return unique_items

    @staticmethod
    def _apply_limit(items: list[dict], limit: int | None) -> list[dict]:
        if limit is None:
            return items
        return items[:limit]

    @staticmethod
    def _scroll_full(page) -> None:
        for _ in range(SCRAPER_CONFIG["scroll_steps"]):
            page.mouse.wheel(0, 1800)
            time.sleep(SCRAPER_CONFIG["scroll_pause_seconds"])