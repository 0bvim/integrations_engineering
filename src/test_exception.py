# test_exceptions.py

from utils import custom_exceptions

def test_raising_exceptions():
    try:
        raise custom_exceptions.ConfigError("This is a test ConfigError.")
    except custom_exceptions.ConfigError as e:
        print(f"Caught ConfigError: {e}")

    try:
        raise custom_exceptions.ClientFileError("Client file not found!")
    except custom_exceptions.ClientFileError as e:
        print(f"Caught ClientFileError: {e}")

    try:
        raise custom_exceptions.TracOSDBError("MongoDB connection failed.")
    except custom_exceptions.TracOSDBError as e:
        print(f"Caught TracOSDBError: {e}")

    try:
        raise custom_exceptions.TranslationError("Invalid data format.")
    except custom_exceptions.TranslationError as e:
        print(f"Caught TranslationError: {e}")

    try:
        raise custom_exceptions.DataValidationError("Invalid date field.")
    except custom_exceptions.DataValidationError as e:
        print(f"Caught DataValidationError: {e}")

if __name__ == "__main__":
    test_raising_exceptions()
