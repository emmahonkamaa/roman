from parser import Parser
from access import aplus_json
from validator import Validator

class CourseData:

    def __init__(self, source):
        self._SOURCE_FOLDER = source
        self._data = {}
        self._config_files = {}
        self._exercise_keys = []
        self._default_lang = None

    def load(self):
        p = Parser(self._SOURCE_FOLDER)
        index = p.parse("index.yaml")
        index = p.process_include(index)
        keys, confs = p.collect_exercise_keys(index)

        config_files = {
            key: p.parse(path)
            for key, path in confs.items()
            }

        self._data = index
        self._config_files = config_files
        self._exercise_keys = keys
        default_lang = index.get("language", None)
        if isinstance(default_lang, list):
            default_lang = default_lang[0]
        self._default_lang = default_lang



    def get_data(self):
        return self._data

    def get_exercise_keys(self):
        return self._exercise_keys

    def get_config_files(self):
        return self._config_files

    def get_def_lang(self):
        return self._default_lang

    def create_aplus_json(self):
        return aplus_json(self)
