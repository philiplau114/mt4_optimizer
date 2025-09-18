def get_stats(numbers):
    if not numbers:
        return {}
    return {
        "min": min(numbers),
        "max": max(numbers),
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers),
        "count": len(numbers)
    }

def is_even(n):
    return n % 2 == 0

def even_numbers(numbers):
    return [n for n in numbers if is_even(n)]