"""
Example Python project for testing Doctown.
"""
from utils import format_output

def calculate_sum(numbers):
    """
    Calculate the sum of a list of numbers.

    Args:
        numbers: List of numbers to sum

    Returns:
        The sum of all numbers
    """
    return sum(numbers)


def main():
    """Main entry point for the application."""
    data = [1, 2, 3, 4, 5]
    result = calculate_sum(data)

    output = format_output(result)
    print(output)


if __name__ == "__main__":
    main()
