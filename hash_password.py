from werkzeug.security import generate_password_hash
import sys


def create_password_hash():
    if len(sys.argv) != 2:
        print("Usage: python hash_password.py <password>")
        print("Example: python hash_password.py admin123")
        return

    password = sys.argv[1]
    hashed = generate_password_hash(password)

    print(f"Password: {password}")
    print(f"Hashed: {hashed}")

    # Also show SQL for easy insertion
    print(f"\nSQL for database:")
    print(f"UPDATE users SET password_hash = '{hashed}' WHERE username = 'admin';")


if __name__ == '__main__':
    create_password_hash()