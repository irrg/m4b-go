from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Book:
    asin: str
    title: str
    authors: list[str]
    runtime_minutes: int


def list_books(page_size: int = 100) -> list[Book]:
    import audible
    from .auth import load_auth

    auth = load_auth()
    books: list[Book] = []
    page = 1

    with audible.Client(auth=auth) as client:
        while True:
            resp = client.get(
                "library",
                params={
                    "num_results": page_size,
                    "page": page,
                    "response_groups": "contributors,product_attrs",
                    "sort_by": "-PurchaseDate",
                },
            )
            items = resp.get("items", [])
            if not items:
                break

            for item in items:
                authors = [
                    c["name"]
                    for c in item.get("authors") or []
                ]
                books.append(Book(
                    asin=item.get("asin", ""),
                    title=item.get("title", ""),
                    authors=authors,
                    runtime_minutes=item.get("runtime_length_min", 0),
                ))

            if len(items) < page_size:
                break
            page += 1

    return books


def find_book(query: str) -> Book | None:
    books = list_books()
    ql = query.lower()
    for b in books:
        if ql in b.title.lower() or b.asin == query:
            return b
    return None
