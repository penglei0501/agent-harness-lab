"""Utility functions for my_package."""


def greet(name: str, greeting: str = "Hello") -> str:
    """Return a greeting message.

    Args:
        name: The name of the person to greet.
        greeting: The greeting word to use (default: "Hello").

    Returns:
        A formatted greeting string.
    """
    return f"{greeting}, {name}!"


def add(a: int | float, b: int | float) -> int | float:
    """Return the sum of two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of a and b.
    """
    return a + b


def is_palindrome(s: str) -> bool:
    """Check if a string is a palindrome (case-insensitive).

    Args:
        s: The string to check.

    Returns:
        True if the string is a palindrome, False otherwise.
    """
    cleaned = s.replace(" ", "").lower()
    return cleaned == cleaned[::-1]
