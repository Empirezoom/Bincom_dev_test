import argparse
import os
import random
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


class ColorTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = None
        self.current_cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.current_row = []
        elif tag == "td" and self.current_row is not None:
            self.current_cell = []

    def handle_data(self, data):
        if self.current_cell is not None:
            self.current_cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.current_cell is not None:
            self.current_row.append("".join(self.current_cell).strip())
            self.current_cell = None
        elif tag == "tr" and self.current_row is not None:
            if len(self.current_row) >= 2:
                self.rows.append(self.current_row)
            self.current_row = None


def read_colors(html_path):
    parser = ColorTableParser()
    parser.feed(Path(html_path).read_text(encoding="utf-8"))
    colors = []
    for row in parser.rows:
        colors.extend(color.strip().upper() for color in row[1].split(","))
    return [color for color in colors if color]


def recursive_search(numbers, target, index=0):
    if index >= len(numbers):
        return -1
    if numbers[index] == target:
        return index
    return recursive_search(numbers, target, index + 1)


def save_frequencies(frequencies, database_url):
    try:
        import psycopg2
    except ImportError as error:
        raise RuntimeError(
            "Install dependencies with: pip install psycopg2-binary"
        ) from error

    with psycopg2.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS shirt_color_frequency (
                       color TEXT PRIMARY KEY,
                       frequency INTEGER NOT NULL
                   )"""
            )
            cursor.executemany(
                """INSERT INTO shirt_color_frequency (color, frequency)
                   VALUES (%s, %s)
                   ON CONFLICT (color) DO UPDATE
                   SET frequency = EXCLUDED.frequency""",
                list(frequencies.items()),
            )


def run_search_prompt():
    numbers = [int(value.strip()) for value in input(
        "Enter integers separated by commas: "
    ).split(",") if value.strip()]
    target = int(input("Enter the number to find: "))
    index = recursive_search(numbers, target)
    if index == -1:
        print("Number not found.")
    else:
        print(f"Number found at index {index}.")


def main():
    argument_parser = argparse.ArgumentParser(
        description="Analyze the dress colors in the local index.html file."
    )
    argument_parser.add_argument(
        "--html",
        default=str(Path(__file__).with_name("index.html")),
        help="Path to the HTML file containing the color table.",
    )
    argument_parser.add_argument(
        "--search",
        action="store_true",
        help="Run the interactive recursive-search example.",
    )
    arguments = argument_parser.parse_args()

    colors = read_colors(arguments.html)
    if not colors:
        raise SystemExit("No color entries were found in the HTML table.")

    frequencies = Counter(colors)
    most_common_color, most_common_count = frequencies.most_common(1)[0]
    sorted_colors = sorted(colors)
    middle = len(sorted_colors) // 2
    if len(sorted_colors) % 2:
        alphabetical_median = sorted_colors[middle]
    else:
        alphabetical_median = sorted(
            (sorted_colors[middle - 1], sorted_colors[middle])
        )[0]

    mean_frequency = len(colors) / len(frequencies)
    frequency_variance = sum(
        (count - mean_frequency) ** 2 for count in frequencies.values()
    ) / len(frequencies)
    red_probability = frequencies.get("RED", 0) / len(colors)

    print(f"Total color entries: {len(colors)}")
    print(f"Mean color: not defined for categorical data; mode is {most_common_color}")
    print(f"Most worn color: {most_common_color} ({most_common_count} times)")
    print(
        "Median color: not intrinsically defined; "
        f"alphabetical median is {alphabetical_median}"
    )
    print(f"Variance of per-color frequencies (population): {frequency_variance:.4f}")
    print(
        f"Probability of red: {frequencies.get('RED', 0)}/{len(colors)} "
        f"= {red_probability:.4%}"
    )

    print("\nColor frequencies:")
    for color, count in sorted(frequencies.items()):
        print(f"{color}: {count}")

    binary_number = "".join(random.choice("01") for _ in range(4))
    print(f"\nRandom 4-digit binary number: {binary_number}")
    print(f"Base 10 value: {int(binary_number, 2)}")

    fibonacci = [0, 1]
    for _ in range(2, 50):
        fibonacci.append(fibonacci[-1] + fibonacci[-2])
    print(f"Sum of the first 50 Fibonacci numbers (starting 0, 1): {sum(fibonacci)}")

    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        save_frequencies(frequencies, database_url)
        print("Color frequencies saved to PostgreSQL.")
    else:
        print("PostgreSQL not updated: set the DATABASE_URL environment variable.")

    if arguments.search:
        run_search_prompt()


if __name__ == "__main__":
    main()