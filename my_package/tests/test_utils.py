"""Tests for my_package.utils."""

from my_package.utils import add, greet, is_palindrome


class TestGreet:
    """Tests for the greet function."""

    def test_default_greeting(self) -> None:
        """Test greet with default greeting."""
        assert greet("World") == "Hello, World!"

    def test_custom_greeting(self) -> None:
        """Test greet with a custom greeting."""
        assert greet("Alice", "Hi") == "Hi, Alice!"

    def test_empty_name(self) -> None:
        """Test greet with an empty string."""
        assert greet("") == "Hello, !"


class TestAdd:
    """Tests for the add function."""

    def test_add_positive(self) -> None:
        """Test adding two positive numbers."""
        assert add(2, 3) == 5

    def test_add_negative(self) -> None:
        """Test adding a negative and a positive number."""
        assert add(-1, 1) == 0

    def test_add_float(self) -> None:
        """Test adding float numbers."""
        assert add(1.5, 2.5) == 4.0


class TestIsPalindrome:
    """Tests for the is_palindrome function."""

    def test_simple_palindrome(self) -> None:
        """Test a simple palindrome word."""
        assert is_palindrome("racecar") is True

    def test_non_palindrome(self) -> None:
        """Test a non-palindrome word."""
        assert is_palindrome("hello") is False

    def test_palindrome_with_spaces(self) -> None:
        """Test a palindrome phrase with spaces."""
        assert is_palindrome("A man a plan a canal Panama") is True

    def test_case_insensitive(self) -> None:
        """Test that palindrome check is case-insensitive."""
        assert is_palindrome("RaceCar") is True

    def test_empty_string(self) -> None:
        """Test that an empty string is considered a palindrome."""
        assert is_palindrome("") is True
