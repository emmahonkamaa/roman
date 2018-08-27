import os, time, json, yaml
import logging
#from setup import here

META = "apps.meta"
INDEX = "index"
logger = logging.getLogger(__name__)


class ParserError(Exception):
    def __init__(self, value, error=None):
        self.value = value
        self.error = error

    def __str__(self):
        if self.error is not None:
            return "%s: %s" % (repr(self.value), repr(self.error))
        return repr(self.value)


class Parser:

    FORMATS = {
        'json': json.load,
        'yaml': yaml.load,
        'yml': yaml.load
    }

    def __init__(self, course_dir):
        '''
        The constructor.
        '''
        self._DIR = course_dir



    def parse(self, path, loader=None):
        '''
        Parses a dict from a file.
        @type path: C{str}
        @param path: a path to a file
        @type loader: C{function}
        @param loader: a configuration file stream parser
        @rtype: C{dict}
        @return: an object representing the configuration file or None
        '''
        if not loader:
            try:
                loader = self.FORMATS[os.path.splitext(path)[1][1:]]
            except:
                raise ParseError('Unsupported format "%s"' % (path))
        data = None
        path = os.path.join(self._DIR, path)
        try:
            with open(path) as f:
                try:
                    data = loader(f)
                except ValueError as e:
                    raise ParseError("Configuration error in %s" % (path), e)
        except OSError as e:
            print(e)

        return data


    def process_include(self, data):
        '''
        Checks for "include" within data and replaces it with appropriate fields.
        @type data: C{dict}
        @param path: dict that might have "include" fields
        @rtype: C{dict}
        @return: the input data with included data
        '''
        if data is None:
            logger.debug("Data is empty!")
            return None

        def rec(m):
            new_data = {}
            if isinstance(m, dict):
                if "include" in m:
                    new_data = self._include(m["include"])
                    m.pop("include")
                    new_data = rec(new_data)
                list_dicts = [o for o in m.items() if isinstance(o[1], dict)]
                for o in list_dicts:
                    m[o[0]] = rec(o[1])
                new_data.update(m)
            if isinstance(m, list):
                new_m = []
                for item in m:
                    new_m.append(rec(item))
                return new_m
            return m

        return rec(data)


    def _include(self, path):
        os.path.join(self._DIR, path)
        data = parse(path)
        return data



    def collect_exercise_keys(self, course):
        '''
        Collects exercise_keys and their config paths from course
        @type course: C{dict}
        @param course: contents of index.yaml (unvalidated?)
        @rtype: C{list}, C{list}
        @return: list with all exercise keys and a dictionary with the data
        read from configuration files
        '''

        exercises = []
        config_files = {}

        def recurse_exercises(parent):
            if not "children" in parent:
                return
            for o in parent["children"]:
                if "key" in o:
                    exercise_key = o["key"]
                    conf = None
                    if "config" in o:
                        conf = o["config"]

                    elif "type" in o and "exercise_types" in course \
                            and o["type"] in course["exercise_types"] \
                            and "config" in course["exercise_types"][o["type"]]:
                        conf = course["exercise_types"][o["type"]]["config"]
                    else:
                        logger.debug("No key found!")
                    if conf:
                        exercises.append(exercise_key)
                        config_files[exercise_key] = conf
                recurse_exercises(o)

        if "modules" in course:
            modules = course["modules"]
            for m in modules:
                recurse_exercises(m)
        return exercises, config_files
