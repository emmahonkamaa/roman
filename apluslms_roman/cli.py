import argparse
from os import getcwd, path
from os.path import abspath, expanduser, expandvars
from sys import exit, stderr, modules
import logging

from . import __version__
from. builder import Engine
from .backends.docker import DockerBackend
from .configuration import CourseConfigError, CourseConfig
from .validator import Validator

LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]

logger = logging.getLogger(__name__)

def main():


    parser = argparse.ArgumentParser(description='Course material builder')
    parser.add_argument('course', nargs='?',
                        help='Location of the course definition. (default: current working dir)')

    parser.add_argument('--version', action='store_true',
                        help='Print version info')
    parser.add_argument("-v", "--verbose", dest="verbose_count",
                        action="count", default=0,
                        help="increases log verbosity for each occurence.")

    args = parser.parse_args()
    logging.basicConfig(
        level=LOG_LEVELS[min(args.verbose_count, 2)],
        #format='%(name)s (%(levelname)s): %(message)s'
    )

    if args.version:
        print("Roman {}\n".format(__version__))

    # Verify engine connection
    engine = Engine()
    error = engine.verify()
    if error:
        print("{} failed to connect. Make sure that you have correct settings."
              .format(engine.backend.__class__.__name__))
        print(" >> {}".format(error))
        if isinstance(engine.backend, DockerBackend):
            print("""
Do you have docker-ce installed and running?
Are you in local 'docker' group? Have you logged out and back in after joining?
You might be able to add yourself to that group with 'sudo adduser docker'.
""")
        exit(0 if args.version else 1)
    elif args.version:
        print(engine.version_info())
        exit(0)

    # read configuraion
    if args.course:
        # Resolve home, vars and relative elements from the course path
        course = abspath(expanduser(expandvars(args.course)))
    else:
        # default to current dir
        course = getcwd()
    try:
        config = CourseConfig.find_from(course)
    except CourseConfigError as e:
        print("Invalid course config: {}".format(e))
        exit(1)

    # create validator (and validate config)
    logging.info("Validation step:")
    validator = Validator(config)
    validator.validate( path.join(getcwd(), "_build/yaml/index.yaml") , "index", 1)
    # build course
    builder = engine.create_builder(config)
    result = builder.build()
    print(result)
    logging.shutdown()
    exit(result.code or 0)



if __name__ == '__main__':
    main()
