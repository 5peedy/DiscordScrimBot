import json
import sys
import os.path


def create_default_config():
    with open("utils/config_default.json") as f:
        content = json.load(f)
        with open("config.json", "w") as config:
            json.dump(content, config, indent=2)
    sys.exit("Default config created. Enter connection parameter in file config.json")


class JsonCon:
    @staticmethod
    def write(file_name, content):
        with open(file_name) as f:
            json.dump(content, f, indent=2)

    @staticmethod
    def load(file_name):
        if os.path.isfile(file_name):
            with open(file_name) as f:
                return json.load(f)
        else:
            return None

    @staticmethod
    def load_config(file_name):
        file = JsonCon.load(file_name)
        if file is None:
            create_default_config()
        else:
            return file
