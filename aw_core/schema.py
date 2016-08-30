import os
import json


def this_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def schema_dir() -> str:
    return os.path.dirname(this_dir())


def get_json_schema(name: str) -> dict:
    with open(os.path.join(schema_dir(), "schemas", name + ".json")) as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    print(get_json_schema("event"))