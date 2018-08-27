from pprint import pprint
from dataset import CourseData
import json

COURSEFOLDER = #FIXME: a path to course/_build/yaml
#"/u/62/honkame2/unix/apluslms/Oppimateriaali/_build/yaml/"


def main():

    course = CourseData(COURSEFOLDER)
    course.load()
    ready = course.create_aplus_json()

    with open("test.json", "w") as f:
        json.dump(ready, f)


main()
