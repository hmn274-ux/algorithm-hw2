"""Compare separate-chaining probe counts with textbook expectations."""

import csv
import random
import sys
from pathlib import Path

# Support invocation as `python3 experiments/probe_experiment.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.hash_table import HashTable

CAPACITY = 4093
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
RANDOM_SEED = 2026
OUTPUT_DIRECTORY = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIRECTORY / "results.csv"
SVG_PATH = OUTPUT_DIRECTORY / "probe_experiment.svg"


def _random_url(generator):
    host = generator.getrandbits(64)
    path = generator.getrandbits(64)
    return f"https://{host:016x}.example/{path:016x}"


def _unique_url(table, generator):
    url = _random_url(generator)
    while url in table:
        url = _random_url(generator)
    return url


def measure_load_factor(target_alpha, generator):
    """Measure successful and unsuccessful node comparisons at one load."""
    table = HashTable(initial_capacity=CAPACITY, max_load=None)
    entry_count = round(CAPACITY * target_alpha)
    inserted_urls = []

    for _ in range(entry_count):
        url = _unique_url(table, generator)
        table[url] = True
        inserted_urls.append(url)

    successful_comparisons = sum(table.probe_count(url) for url in inserted_urls)
    successful_average = successful_comparisons / entry_count

    miss_count = max(1000, entry_count)
    unsuccessful_comparisons = 0
    for _ in range(miss_count):
        url = _unique_url(table, generator)
        unsuccessful_comparisons += table.probe_count(url)
    unsuccessful_average = unsuccessful_comparisons / miss_count

    actual_alpha = len(table) / table.capacity
    return {
        "target_alpha": target_alpha,
        "actual_alpha": actual_alpha,
        "entries": len(table),
        "successful_average": successful_average,
        "successful_theory": 1 + actual_alpha / 2,
        "unsuccessful_average": unsuccessful_average,
        "unsuccessful_theory": actual_alpha,
    }


def _write_csv(rows, path):
    fields = (
        "target_alpha",
        "actual_alpha",
        "entries",
        "successful_average",
        "successful_theory",
        "unsuccessful_average",
        "unsuccessful_theory",
    )
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.6f}" if isinstance(value, float) else value
                    for key, value in row.items()
                }
            )


def _write_svg(rows, path):
    width = 1000
    height = 560
    left = 80
    top = 70
    plot_width = 700
    plot_height = 410
    bottom = top + plot_height
    right = left + plot_width
    max_y = max(
        row[key]
        for row in rows
        for key in ("successful_average", "unsuccessful_average",
                    "successful_theory", "unsuccessful_theory")
    )
    y_limit = max(1, int(max_y) + 1)

    def x_position(alpha):
        return left + (alpha - LOAD_FACTORS[0]) / (
            LOAD_FACTORS[-1] - LOAD_FACTORS[0]
        ) * plot_width

    def y_position(value):
        return bottom - value / y_limit * plot_height

    series = (
        ("successful_average", "Successful measured", "#2563eb", ""),
        ("successful_theory", "Successful theory", "#60a5fa", "8 5"),
        ("unsuccessful_average", "Unsuccessful measured", "#dc2626", ""),
        ("unsuccessful_theory", "Unsuccessful theory", "#f87171", "8 5"),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="80" y="35" font-family="sans-serif" font-size="20">'
        "Separate chaining probe counts vs load factor</text>",
    ]

    for tick in range(y_limit + 1):
        y = y_position(tick)
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" '
            'stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" '
            'font-family="sans-serif" font-size="12">'
            f"{tick}</text>"
        )

    for alpha in range(0, 5):
        if alpha < LOAD_FACTORS[0]:
            continue
        x = x_position(alpha)
        parts.append(
            f'<text x="{x:.2f}" y="{bottom + 24}" text-anchor="middle" '
            'font-family="sans-serif" font-size="12">'
            f"{alpha}</text>"
        )

    parts.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" '
            'stroke="#111827"/>',
            f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" '
            'stroke="#111827"/>',
            f'<text x="{left + plot_width / 2}" y="{height - 18}" '
            'text-anchor="middle" font-family="sans-serif" font-size="14">'
            "Load factor (alpha)</text>",
            f'<text x="20" y="{top + plot_height / 2}" '
            'transform="rotate(-90 20 '
            f'{top + plot_height / 2})" text-anchor="middle" '
            'font-family="sans-serif" font-size="14">'
            "Average node comparisons</text>",
        )
    )

    for index, (field, label, color, dash) in enumerate(series):
        points = [
            (x_position(row["target_alpha"]), y_position(row[field]))
            for row in rows
        ]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<polyline points="{point_string}" fill="none" stroke="{color}" '
            f'stroke-width="2"{dash_attribute}/>'
        )
        for x, y in points:
            parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.5" fill="{color}"/>'
            )
        legend_y = top + 20 + index * 26
        parts.append(
            f'<line x1="{right + 24}" y1="{legend_y}" '
            f'x2="{right + 58}" y2="{legend_y}" stroke="{color}" '
            f'stroke-width="2"{dash_attribute}/>'
        )
        parts.append(
            f'<text x="{right + 66}" y="{legend_y + 4}" '
            'font-family="sans-serif" font-size="12">'
            f"{label}</text>"
        )

    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    generator = random.Random(RANDOM_SEED)
    rows = [
        measure_load_factor(alpha, generator)
        for alpha in LOAD_FACTORS
    ]
    _write_csv(rows, CSV_PATH)
    _write_svg(rows, SVG_PATH)

    print(
        "Target α | Actual α | Successful avg/theory | "
        "Unsuccessful avg/theory"
    )
    for row in rows:
        print(
            f"{row['target_alpha']:8.2f} | {row['actual_alpha']:8.4f} | "
            f"{row['successful_average']:7.3f} / "
            f"{row['successful_theory']:7.3f} | "
            f"{row['unsuccessful_average']:7.3f} / "
            f"{row['unsuccessful_theory']:7.3f}"
        )
    print(f"\nCSV: {CSV_PATH}")
    print(f"SVG: {SVG_PATH}")


if __name__ == "__main__":
    main()
