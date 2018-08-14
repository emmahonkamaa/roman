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


    def _process_include(self, data):
        '''
        Checks for "include" within data and replaces it with appropriate fields.
        @type data: C{dict}
        @param path: contents of index.yaml
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
                for o in [o for o in m.items() if isinstance(o[1], dict)]:
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
        #check stuff
        os.path.join(self._DIR, path)
        data = parse(path)
        return data



    def collect_exercise_keys(self, course):
        '''
        Collects exercise_keys and their config paths from courses.
        @type course: C{dict}
        @param course: contents of index.yaml (unvalidated)
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




    #
    # def _process_exercise_data(self, course_root, data):
    #     default_lang = course_root['lang']
    #     lang_keys = []
    #     tags_processed = []
    #
    #     def recursion(n, lang, collect_lang=False):
    #         t = type(n)
    #         if t == dict:
    #             d = {}
    #             for k,v in n.items():
    #                 m = self.PROCESSOR_TAG_REGEX.match(k)
    #                 while m:
    #                     k, tag = m.groups()
    #                     tags_processed.append(tag)
    #                     if collect_lang and tag == 'i18n' and type(v) == dict:
    #                         lang_keys.extend(v.keys())
    #                     if tag not in self.TAG_PROCESSOR_DICT:
    #                         raise ConfigError('Unsupported processor tag "%s"' % (tag))
    #                     v = self.TAG_PROCESSOR_DICT[tag](d, n, v, lang=lang)
    #                     m = self.PROCESSOR_TAG_REGEX.match(k)
    #                 d[k] = recursion(v, lang, collect_lang)
    #             return d
    #         elif t == list:
    #             return [recursion(v, lang, collect_lang) for v in n]
    #         else:
    #             return n
    #
    #     default = recursion(data, default_lang, True)
    #     root = { default_lang: default }
    #     for lang in (set(lang_keys) - set([default_lang])):
    #         root[lang] = recursion(data, lang)
    #
    #     LOGGER.debug('Processed %d tags.', len(tags_processed))
    #     return root
    # #
    #
    # def exercise_entry(self, course, exercise_key, lang=None):
    #     exercise_root = _make_exercise_data(course)
    #     if not exercise_root or "data" not in exercise_root or not exercise_root["data"]:
    #         return course["data"], None
    #     if lang == '_root':
    #         return course["data"], exercise_root["data"]
    #
    #     for lang in (lang, course["lang"]):
    #         if lang in exercise_root["data"]:
    #             return course["data"], exercise_root["data"][lang]
    #
    #     return course["data"], list(exercise_root["data"].values())[0]
    #
    #
    #
    # def load_exercise(self, exercise_key, course):
    #     file_name = exercise_key
    #     if "config_files" in course:
    #         file_name = course["config_files"].get(exercise_key, exercise_key)
    #     if file_name.startswith("/"):
    #         f, data = _exercise_loader(course, file_name[1:],
    #                     self._conf_dir(DIR, course["data"]["key"], {}))
    #     else:
    #         f, data = _exercise_loader(course, file_name,
    #                     self._conf_dir(DIR, course["data"]["key"], course["meta"]))
    #     if not data:
    #         return None
    #
    #     #tähän vielä: kieliversiot
    #
    # def _default_lang(self, data):
    #     l = data.get('lang')  #koska ei enää tueta 'language'-kenttää!!
    #     if type(l) == list:
    #         data['lang'] = l[0]
    #     elif l == str:
    #         data['lang'] = l
    #     return data.get('lang', DEFAULT_LANG)
    #
    # def _exercise_loader(self, course, exercise_key, course_dir):
    #     conf = self._get_config(os.path.join(course_dir, exercise_key))
    #     #Tässä: validate conf
    #     data = parse(conf)
    #     #if "include" in data:
    #     #  jätetään myöhemmälle
    #     return conf, data
    #
    # def _conf_dir(self, directory, course_key, meta):
    #     if 'grader_config' in meta:
    #         return os.path.join(directory, course_key, meta['grader_config'])
    #     return os.path.join(directory, course_for o in [o for o in m.items() if isinstance(o[1], dict):key)
    #
    # def _get_config(self, path):
    #     if os.path.isfile(path):
    #         ext = os.path.splittext(path)[1]
    #         if len(ext) > 0 and ext[1:] in self.FORMATS:
    #             return path
    #     config_file = None
    #     if os.path.isdir(os.path.dirname(path)):
    #         for ext in self.FORMATS.keys():
    #             f = "%s.%s" % (path, ext)
    #             if os.path.isfile(f):
    #                 if config_file != None:
    #                     raise ConfigError('Multiple config files for "%s"' % (path))
    #                 config_file = f
    #     if not config_file:
    #         raise ConfigError('No supported config at "%s"' % (path))
    #     return config_file
    #
    #
    #
    #
    #
    #
    #
    #for o in [o for o in m.items() if isinstance(o[1], dict):
    #
    #
    #
    #
    #
    #
    #
    #
    #
    # def course_entry(self, course_key):
    #     root = self._course_root(course_key)
    #     return None if root is None else root['data']
    #
    # def _course_root(self, course_key):
    #     meta = read_meta(os.path.join(DIR, course_key, META))
    #     if 'grader_config' in meta:
    #         conf_dir = os.path.join(DIR, course_key, meta['grader_config'])
    #     else:
    #         conf_dir = os.path.join(DIR, course_key)
    #
    #     try:
    #         f = self._get_config(os.path.join(conf_dir, INDEX))
    #     except ConfigError:
    #         return None
    #
    #     data = self._parse(f)
    #     if data is None:
    #         raise Error('Failed to parse config') #TODO
    #
    #     self._check_fields(f, data, ["name"])
    #     data['key'] = course_key
    #     data['dir'] = self._conf_dir(DIR, course_key, {})
    #
    #     if 'static_url' not in data:
    #         data['static_url'] = 0#???
    #
    #     if 'modules' in data:
    #         keys = []
    #         config = {}
    #
    #         def exercise_recursion(parent):
    #             if "children" in parent:
    #                 for exercise_vars in parent["children"]:
    #                     if "key" in exercise_vars:
    #                         exercise_key = str(exercise_vars["key"])
    #                         cfg = None
    #                         if "config" in exercise_vars:
    #                             cfg = exercise_vars["config"]
    #                         elif:
