import yaml
from jsonschema import validate
import re
import os
#from operator import itemgetter
import logging

logger = logging.getLogger(__name__)

#mystinen lista schema directoryja - course.yamlissa jossain kentässä, joka sijaitsee käyttäjän paketin juuressa
def get_folders(config):
    folders = config.__config__.get("custom_schema_locations", [])
    dir_, _ = os.path.split(__file__)
    folders.append(os.path.join(dir_, "schemas"))
    return folders


#idea = { schema_name: {(major, minor): location}}
schema_index = {}

class Validator:
    def __init__(self, config):
        logger.info(" Creating validator.")
        self.folders = get_folders(config)
        logger.info(" Validator ready.")

    def validate(self, filename, schema, major=1, minor=float('inf')):
        logger.info(" Preparing to validate %s...", filename)
        logger.info(" Locating all valid schemas...")
        self.find_all_matches(schema)
        logger.info(" Locating matching version v%d...", major)
        serial, ext = self.find_newest(schema, major, minor)
        schema_fullname = "{}_v{}_{}.{}".format(schema, serial[0], serial[1], ext[1])
        logger.debug(" Using schema: %s", schema_fullname)
        schema_path = os.path.join(ext[0], schema_fullname)
        logger.info(" Starting validation of %s with %s", filename, schema_fullname)
        result = self.assert_valid(schema_path, filename)
        logger.info(" Validation done", filename)
        return result

    def find_all_matches(self, schema):
        prog = re.compile("{}_v(\d+)_(\d+).(yaml|yml|json)".format(schema))
        logger.debug(" Schema-------------%s", schema)
        for folder in self.folders:
            logger.debug(" Folder-------------%s",  folder)
            for ff in os.listdir(folder):
                logger.debug(" File-------------%s",  ff)
                if prog.match(ff) is not None:
                    found = prog.match(ff).groups()
                    schema_index.setdefault(schema, {})
                    logger.debug(" Index-------------%s",  schema_index)
                    current = schema_index[schema].setdefault((int(found[0]), int(found[1])), None)
                    if current is None:
                        schema_index[schema][int(found[0]), int(found[1])] = (folder, found[2])
                    #matches.append([schema, int(found[0]), int(found[1]), found[2] , folder])
        print(schema_index)

    #Finds the newest schema with 'major' and 'minor' as maximum allowed values.
    #If major is not defined, v1.x is assumed.
    def find_newest(self, schema, major, minor):
        schemas = schema_index.get(schema)
        if schemas is None:
            print("No schema's with that name!")
            return None

        #filter(_ <= major.minor) and reduce(max(_,_))
        i = {k:v for k, v in schemas.items() if k[0]<major or k[0]==major and k[1]<=minor}
        (ans, f) = ((0,0), None)
        for k, v in i.items():
            (ans, f) = (k, v) if k[0]>ans[0] or k[0]==ans[0] and k[1]>ans[1] else (ans, f)
        return (ans, f)

    #Validate schema
    def assert_valid(self, schema, filename):
        try:
            with open(filename, "r") as f:
                ff = f.read()
            with open(schema, "r") as s:
                ss = s.read()
        except:
            logger.exception('Error with files, exiting....')
            return

        logger.info('Files opened succesfully. Validating...')
        validate(yaml.safe_load(ff), yaml.safe_load(ss))
        logger.info('Done')

    # def get_schema_folder_and_type(self, schema, serial):
    #     return schema_index.get(schema).get(serial)
    #
    # def get_schema_name_from_file(self, filename):
    #     prog = re.compile("^\/(.+\/)*(.+)\.(json|yaml|yml)$")
    #     name = prog.match(filename).groups()[1]
    #     return name
