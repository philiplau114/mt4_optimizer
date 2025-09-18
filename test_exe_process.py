import sys
import json
from math_utils import get_stats, even_numbers

def main():
    if len(sys.argv) > 1:
        try:
            numbers = [float(x) for x in sys.argv[1:]]
        except ValueError:
            print(json.dumps({"error": "Arguments must be numbers"}))
            return
    else:
        print(json.dumps({"error": "No numbers provided"}))
        return

    stats = get_stats(numbers)
    evens = even_numbers(numbers)

    result = {
        "stats": stats,
        "even_numbers": evens
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()