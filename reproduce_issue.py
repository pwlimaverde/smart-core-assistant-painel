import ast
import json


def test_literal_eval():
    print("Testing ast.literal_eval with JSON string...")

    # Simulate the data that might be in params
    params = {
        "contact_id": 123,
        "is_active": True,  # This becomes 'true' in JSON
        "data": None,  # This becomes 'null' in JSON
    }

    # Current implementation uses json.dumps
    args_str = json.dumps([params])
    print(f"String stored in DB: {args_str}")

    try:
        # This is what django-q does
        result = ast.literal_eval(args_str)
        print(f"Success! Result: {result}")
    except ValueError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Caught unexpected error: {e}")

    print("\nTesting fix with repr()...")
    # Proposed fix: pass simple int and use repr or just string conversion for simple types
    contact_id = 123
    args_str_fix = repr([contact_id])
    print(f"String stored in DB (fix): {args_str_fix}")

    try:
        result = ast.literal_eval(args_str_fix)
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Caught unexpected error with fix: {e}")


if __name__ == "__main__":
    test_literal_eval()
