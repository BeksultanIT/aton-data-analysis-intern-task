import argparse
import sqlite3
import textwrap


def search(db_path: str, query: str, limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            d.id,
            d.file_name,
            d.extension,
            d.file_path,
            d.source_archive,
            d.size_bytes,
            d.modified_at,
            snippet(documents_fts, 1, '[', ']', '...', 20) AS snippet
        FROM documents_fts
        JOIN documents d ON d.id = documents_fts.rowid
        WHERE documents_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def print_results(results: list[dict], query: str):
    if not results:
        print(f"По запросу «{query}» ничего не найдено.")
        return

    print(f"\nНайдено результатов: {len(results)} (по запросу «{query}»)\n")
    print("─" * 70)

    for i, r in enumerate(results, 1):
        archive_info = f" [из архива: {r['source_archive']}]" if r["source_archive"] else ""
        print(f"{i}. {r['file_name']} (.{r['extension']}){archive_info}")
        print(f"   Путь: {r['file_path']}")
        print(f"   Размер: {r['size_bytes']:,} байт | Изменён: {r['modified_at']}")
        if r.get("snippet"):
            wrapped = textwrap.fill(r["snippet"], width=66, initial_indent="   ")
            print(f"   Контекст: {wrapped}")
        print("─" * 70)


def main():
    parser = argparse.ArgumentParser(description="Поиск по FTS-базе краулера")
    parser.add_argument("--query", required=True, help="Поисковый запрос (FTS5 синтаксис)")
    parser.add_argument("--db",    default="output/fti.db", help="Путь к SQLite базе")
    parser.add_argument("--limit", type=int, default=10, help="Максимальное число результатов")
    args = parser.parse_args()

    try:
        results = search(args.db, args.query, args.limit)
        print_results(results, args.query)
    except Exception as e:
        print(f"Ошибка: {e}")
        raise


if __name__ == "__main__":
    main()