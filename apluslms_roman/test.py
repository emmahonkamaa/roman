from parser import Parser
from access import aplus_json
from pprint import pprint
import json

COURSEFOLDER = "/u/62/honkame2/unix/apluslms/Oppimateriaali/_build/yaml/"
def parse_and_collect(folder):
    p = Parser(folder)
    index = p.parse("index.yaml")
    index2 = p._process_include(index)
    keys, confs = p.collect_exercise_keys(index)
    # c = {}
    # for key, path in confs.items():
    #     c[key] = p.parse(path)

    config_files = {
        key: p.parse(path)
        for key, path in confs.items()
        }

    data = {}
    data["index"] = index2
    data["config_files"] = config_files
    data["exercise_keys"] = keys
    if "language" in index2:
        l = index2["language"]
        if type(l) == list:
            l = l[0]
        data["default_lang"] = l

    return data

def main():
    data = parse_and_collect(COURSEFOLDER)
    jsonn = aplus_json(data)
    with open("test.json", "w") as f:
        json.dump(jsonn, f)


main()
