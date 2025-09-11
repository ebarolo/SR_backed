import argparse
import json
from pathlib import Path


def convert_jsonl_to_array(src: Path, dst: Path, indent: int = 2, strict: bool = True) -> None:
    """
    Convert a JSON Lines (NDJSON) log file into a single valid JSON array file.

    - Streams line-by-line to avoid high memory usage.
    - Skips empty lines. Fails on invalid JSON unless strict=False.
    """
    with src.open("r", encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
        fout.write("[\n")
        first = True
        for idx, line in enumerate(fin, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as e:
                msg = f"Linea {idx}: JSON non valido: {e}"
                if strict:
                    raise ValueError(msg) from e
                else:
                    # Linea ignorata in modalità non-strict
                    continue

            if not first:
                fout.write(",\n")
            else:
                first = False

            json.dump(obj, fout, ensure_ascii=False, indent=indent)

        fout.write("\n]\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converte un file di log JSONL (NDJSON) in un singolo JSON valido (array)."
    )
    parser.add_argument("src", type=Path, help="Percorso del file sorgente (JSONL)")
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        help="Percorso del file di output (default: <src>.formatted.json)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentazione dell'output JSON (default: 2)",
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Ignora le righe non valide invece di fallire",
    )
    args = parser.parse_args()

    src: Path = args.src
    if not src.exists():
        raise SystemExit(f"Sorgente non trovato: {src}")

    out: Path = args.out or src.with_suffix(src.suffix + ".formatted.json")
    convert_jsonl_to_array(src, out, indent=args.indent, strict=not args.no_strict)
    print(f"Creato JSON valido: {out}")


if __name__ == "__main__":
    main()

