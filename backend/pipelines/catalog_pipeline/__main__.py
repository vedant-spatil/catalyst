from __future__ import annotations

import argparse
import logging
import sys

from catalog_pipeline.config import load_config
from catalog_pipeline.discovery import list_playlists, search_catalog
from catalog_pipeline.extract import extract
from catalog_pipeline.load import load_landing
from catalog_pipeline.login import run_login
from catalog_pipeline.runner import run
from catalog_pipeline.transform import transform
from warehouse.apply_migrations import apply_migrations

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="catalog_pipeline")
    parser.add_argument(
        "command",
        choices=["login", "playlists", "search", "extract", "load", "transform", "run", "migrate"],
    )
    parser.add_argument("--q", dest="query", default="")
    args = parser.parse_args(argv)

    if args.command == "login":
        run_login()
        return
    if args.command == "playlists":
        list_playlists()
        return
    if args.command == "search":
        if not args.query:
            print("search requires --q", file=sys.stderr)
            raise SystemExit(1)
        search_catalog(args.query)
        return
    if args.command == "migrate":
        cfg = load_config(require_database=True)
        apply_migrations(cfg.database_url)
        print("migrations ok")
        return
    if args.command == "extract":
        result = extract()
        print(result)
        return
    if args.command == "load":
        print(load_landing())
        return
    if args.command == "transform":
        print(transform())
        return
    if args.command == "run":
        run()
        print("run complete")
        return


if __name__ == "__main__":
    main()
