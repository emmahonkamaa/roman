import yaml
from jsonschema import validate, ValidationError
import re
import os
import logging

logger = logging.getLogger(__name__)

#List of (possible) custom schema locations will be in config file
def get_folders(config):
    folders = config.__config__.get("schema_path", [])
    if not isinstance(folders, list):
        raise ValueError("Invalid type for 'schema_path' in config. Excpected a list.")
    dir_, _ = os.path.split(__file__)
    folders.append(os.path.join(dir_, "schemas"))
    return folders

#Format of index:  { schema_name: {(major, minor): full_filepath}}
SCHEMA_INDEX = {}

class Validator:
    def __init__(self, config):
        logger.info(" Creating validator.")
        self.folders = get_folders(config)
        logger.info(" Validator ready.")

    def validate(self, filename, schema, major=1, minor=None):
        logger.info(" Preparing to validate %s...", filename)
        logger.info(" Locating all valid schemas...")
        self.find_all_matches(schema)
        logger.info(" Locating matching version v%d...", major)
        serial, schema_path = self.find_newest(schema, major, minor)
        #schema_fullname = "{}_v{}_{}".format(schema, serial[0], serial[1])
        #schema_path = os.path.join(ext[0], schema_fullname)
        logger.info(" Starting validation of %s with %s", filename, schema_path)
        return self.assert_valid(schema_path, filename)


    def find_all_matches(self, schema):
        prog = re.compile("{}_v(\d+)_(\d+).(yaml|yml|json)".format(schema))
        logger.debug(" Looking for schema-------------%s", schema)
        for folder in self.folders:
            logger.debug(" Folder-------------%s",  folder)
            for ff in os.listdir(folder):
                logger.debug(" File-------------%s",  ff)
                if prog.match(ff) is not None:
                    major, minor, ext = prog.match(ff).groups()
                    schema_i = SCHEMA_INDEX.setdefault(schema, {})
                    logger.debug(" Index-------------%s",  SCHEMA_INDEX)
                    current = schema_i.setdefault((int(major), int(minor)), None)
                    if current is None:
                        schema_i[int(major), int(minor)] = os.path.join(folder, ff)

    #Finds the newest schema with given 'major' and newest 'minor'.
    #If major is not defined, v1 is assumed.
    def find_newest(self, schema, major, minor):
        schemas = SCHEMA_INDEX.get(schema)
        if schemas is None:
            logger.warning(" No schema's with that name!")
            return None

        if minor is None:
            ver = max({v for v in schemas if v[0]==major}, default=None)
            if ver is None:
                logger.warning(" No schema with version %d", major)
                return None
        else:
            ver = (major, minor)

        _file = schemas.get(ver, None)
        if _file is None:
            logger.warning(" No schema with version %d.%d", major, minor)
            return None
        return ver, _file


    #Validate schema
    def assert_valid(self, schema, filename):
        try:
            with open(filename, "r") as f:
                ff = f.read()
            with open(schema, "r") as s:
                ss = s.read()
        except:
            logger.exception(' Error with files, exiting....')
            return False

        try:
            logger.info(' Files opened succesfully. Validating...')
            validate(yaml.safe_load(ff), yaml.safe_load(ss))
            logger.info(' %s validated succesfully', filename)
            return True
        except ValidationError as e:
            logger.warning(" An error occurred!")
            logger.warning(" %s", e)
            return False
