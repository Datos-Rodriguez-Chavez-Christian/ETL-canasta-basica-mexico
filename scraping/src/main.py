import argparse
import traceback

from config import STORE_CONFIGS
from export import export_products, export_summary
from scraper import ProductScraper
from utils import ensure_directories


DEFAULT_STORE_ORDER = [
    "soriana",
    "chedraui"
]


def get_available_store_order() -> list[str]:
    return [
        store_key
        for store_key in DEFAULT_STORE_ORDER
        if store_key in STORE_CONFIGS
    ]


def parse_args() -> argparse.Namespace:
    available_stores = get_available_store_order()

    parser = argparse.ArgumentParser(description="Scraper de productos de canasta básica")

    parser.add_argument(
        "--store",
        default="all",
        choices=["all"] + available_stores,
        help="Tienda a procesar. Si no se especifica, corre todas en orden.",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Ejecuta el navegador sin ventana visible",
    )

    parser.add_argument(
        "--limit-level-1",
        type=int,
        default=None,
        help="Límite temporal para refinamientos nivel 1",
    )

    parser.add_argument(
        "--limit-level-2",
        type=int,
        default=None,
        help="Límite temporal para refinamientos nivel 2",
    )

    return parser.parse_args()


def run_store(
    store_key: str,
    headless: bool,
    limit_level_1: int | None,
    limit_level_2: int | None,
) -> None:
    store_name = STORE_CONFIGS[store_key]["store_name"]

    print("\n" + "#" * 90)
    print(f"INICIANDO TIENDA: {store_name}")
    print("#" * 90)

    scraper = ProductScraper(store_key=store_key, headless=headless)

    products, summary_rows = scraper.run(
        limit_level_1=limit_level_1,
        limit_level_2=limit_level_2,
    )

    products_path = export_products(store_key, products)
    summary_path = export_summary(summary_rows)

    print("\n" + "=" * 80)
    print(f"Tienda procesada: {store_name}")
    print(f"Productos guardados: {len(products)}")
    print(f"CSV productos: {products_path}")
    print(f"CSV resumen: {summary_path}")


def main() -> None:
    args = parse_args()
    ensure_directories()

    if args.store == "all":
        stores_to_run = get_available_store_order()
    else:
        stores_to_run = [args.store]

    print("\nTiendas a procesar:")
    for store_key in stores_to_run:
        print(f"- {STORE_CONFIGS[store_key]['store_name']}")

    for store_key in stores_to_run:
        try:
            run_store(
                store_key=store_key,
                headless=args.headless,
                limit_level_1=args.limit_level_1,
                limit_level_2=args.limit_level_2,
            )

        except Exception as exc:
            store_name = STORE_CONFIGS[store_key]["store_name"]
            print("\n" + "!" * 90)
            print(f"ERROR GENERAL EN TIENDA: {store_name}")
            print(exc)
            print("Se continúa con la siguiente tienda si existe.")
            print("!" * 90)
            traceback.print_exc()


if __name__ == "__main__":
    main()