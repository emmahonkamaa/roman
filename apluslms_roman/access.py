import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

indexFields =  ["name", "description", "lang", "contact", "assistants", "start",
                "end", "categories", "numerate_ignoring_modules"]
moduleFields = ["key", "name", "order", "status", "points_to_pass",
                "introduction", "open", "close", "duration", "late_close",
                "late_duration", "late_penalty"]
exerciseFields = ["key", "title", "name", "category", "max_submisions", "max_points",
                "points_to_pass", "allow_assistant_grading", "status",
                "use_wide_column", "allow_asistant_viewing", "min_group_size",
                "max_group_size", "difficulty", "order", "audience", "description" ]
#Puuttuu: url, exercise_info, model_answer, exercise_template

STATIC = 'http://grader.fi/'
KEY = 'placeholder'
#systeemi menee about:

   # ---- parse index.yaml (and update with "include"-fields)
   # ---- validate index.yaml
   # ----> Meillä on nyt index (dict)

   # ---- aplus_json(index)
   # ----> data (dict)




def aplus_json(course):
    '''
    Takes a dict and formats it to the form that aplus uses.
    @type course: C{dict}
    @param course: contents of index.yaml
    '''
    index = course["index"]
    def_lang = course["default_lang"]
    print(def_lang)
    data = {}
    _copy_fields(data, index, indexFields)
    if "language" in index:
        data["lang"] = deepcopy(index["language"])



    def children_recursion(parent):
        if not "children" in parent:
            return []
        result = []
        for o in [o for o in parent["children"] if "key" in o]:
            of =_type_dict(o, index.get("exercise_types", {}))
            if "config" in of:
                of = _process_config_data(of, course, def_lang)#on tehtävä, jos sisältää "config"?
                of = _get_url_to_exercise(of)
            elif "static_content" in of:  #static content -> luku
                 of = _get_url_to_static(of, index)
            of["children"] = children_recursion(o)
            result.append(of)
        return result

    modules = []
    if 'modules' in index:
        for m in index['modules']:
            mf = _type_dict(m, index.get("module_types", {}))
            mf["children"] = children_recursion(m)
            modules.append(mf)
    data["modules"] = modules

    #mites "gitmanager?"
    #if "gitmanager" in settings.INSTALLED_APPS:
    #   data["build_log_url"] = request.build_absolute_uri(reverse("build-log-json", args=(course_key, )))
    return data

def _process_config_data(of, course, lang):
    config_file = of.pop("config")
    exercise = {}
    new_data = {}
    if "key" in of and of["key"] in course["exercise_keys"]:
        exercise = course["config_files"][of["key"]]
        #_copy_fields(new_data, exercise, ["description", "title" ])
        new_data.update(of)
        #return new_data
        print(of['key'])
        if exercise is None:
            return new_data

        if not 'title' in of and not 'name' in of:
            _copy_fields(new_data, exercise, ['title'])
        if not 'description' in of:
            new_data['description'] = exercise.get('description', '')


        form, i18n = form_fields(exercise, lang)
        print("ok", i18n)
        new_data['exercise_info'] = {
            'form_spec': form,
            'form_i18n': i18n,
        }

        if 'radar_info' in exercise:
            new_data['exercise_info']['radar'] = exercise['radar_info']

        if 'model_answer' in exercise:
            new_data['model_answer'] = exercise['model_answer']
        #TODO elif model_files  and elif createForm

        if 'exercise_template' in exercise:
            new_data['exercise_template'] = exercise['exercise_template']
        #TODO elif template_files





        #tässä: hae configista halutut kentät
        return new_data

    else:
        logger.warning("Avain ei %s löydy!", of["key"])
        return of

def form_fields(exercise, lang):
    form = []
    i18n = {}

    def i18n_map(value):
        if value is "" :
            return ""
        key = value
        if key in i18n:

            raise exception ("Label must be unique, %s alreayd exists in this exercise.", key)
        i18n[key] = value
        return key

    def i18n_m(field):
        key = field
        if type(field) == dict:
            l,d = zip(*field.items())
            if lang in l:
                #print("ok")
                key = field[lang]
            else:
                key = d[0]
        elif type(field) is not str:
            print("???")

        while key in i18n:
            key += "_duplicate"
            #raise exception ("Label must be unique, %s alreayd exists in this exercise.", key)
        i18n[key] = field
        return key




    def field_spec(f, n):
        field = {
            'key': f.get('key', 'field_' + str(n)),
            'type': f.get('type'),
            'title': f.get('title', ''),
            'required': f.get('required', False),
        }
        mods = f.get('compare_method', '').split('-')
        if 'int' in mods or 'float' in mods:
            field['type'] = 'number'

        if 'more' in f:
            field['description'] = i18n_m(f.get('more', ''))
        if 'more|i18n' in f:
            # desc = f.get('more|i18n', {})
            # if type(desc) == dict:
            #     l,d = zip(*desc.items())
            #     desc = d[0]
            field['description'] = i18n_m(f.get('more|i18n', {}))

        if 'options' in f:
            titleMap = {}
            enum = []
            m = 0
            for o in f.get('options', []):
                v = o.get('value', 'option_' + str(m))
                m += 1
                titleMap[v] = i18n_m(o.get('label', o.get('label|i18n', '')))
                enum.append(v)
            field['titleMap'] = titleMap
            field['enum'] = enum

        if 'extra_info' in f:
            extra = f.get('extra_info', '')
            for key in ['validationMessage']:
                if key in extra:
                    extra[key] = i18n_m(extra.get('key', ''))
            field.update(extra)
        if 'class' in field:
            field['htmlClass'] = field['class']
            del(field['class'])

        return field

    t = exercise.get("view_type", None)
    if t == 'access.types.stdsync.createForm':
        n = 0
        for fgs in exercise.get("fieldgroups", []):
            for fs in fgs.get('fields', []):
                t = fs.get('type', None)
                if t == 'table-radio' or t == 'table-checkbox':
                    logger.debug("Found 'table-radio'!")

                else:
                    form.append(field_spec(fs, n))
                    n += 1



    elif t == 'access.types.stdasync.acceptPost':
        for f in exercise.get('fields', []):
            form.append({
                'key': f.get('name'),
                'type': 'textarea',
                'title': i18n_m(f.get('title', '')),
                'required': f.get('required', False),
            })

    elif t == 'access.types.stdasync.acceptFiles':
        for f in exercise.get("files", []):
            form.append({
                'key': f.get('field', ''),
                'type': 'file',
                'title': i18n_m(f.get('name', {})),
                'required': f.get('required', True)
            })

    return form, i18n

def list_get(dicts, key, default):
   return [
        d.get(key, default)
        for d in dicts
    ]


def i18n_get(languages, values, key):
    if len(languages) == 1:
        return values[0].get(key)
    return {
        l: values[i].get(key)
        for i,l in enumerate(languages)
}

def _get_url_to_exercise(data):
    #run service that generates url.
    #for now we use placeholder:
    if 'url' not in data:
        data['url'] = "http://grader.fi/" + data['key']
    return data


def _get_url_to_static(data, index):
    #for now, STATIC contains a placeholder
    path = data.pop('static_content')
    if type(path) == dict:
        data['url'] = {
            lang: '{}{}/{}'.format(STATIC, KEY, p)
            for lang, p in path.items()
        }
    else:
        data['url'] = '{}{}/{}'.format(STATIC, KEY, path)
    return data



def _copy_fields(result, dict_item, pick_fields):
    if dict_item is None:
        return
    for name in pick_fields:
        if name in dict_item:
            result[name] = deepcopy(dict_item[name])


def _type_dict(dict_item, dict_types):
    base = {}
    if "type" in dict_item and dict_item["type"] in dict_types: #jos o:n "type" on dict_typesissä
        base = deepcopy(dict_types[dict_item["type"]])
    base.update(dict_item) # lisätään sinne
    if "type" in base:
        del base["type"]
    return base




























#
#
#
#
# def url_to_exercise(request, course_key, exercise_key):
#     return request.build_absolute_uri(
#         reverse('exercise', args=[course_key, exercise_key]))
#
#
# def export_chapter(course, of):
#     path = of.pop('static_content')
#     if type(path) == dict:
#         of['url'] = {
#             lang: url_to_static(----, course['key'], p) #TODO: muokkaa tässä url!!
#             for lang, p in path.items()
#         }
#     else:
#         of['url'] = url_to_static(----, course['key'], path) #TODO: ks yllä
#     return of
#
# def export_exercise(course, exercise_root, of):
#     of.pop('config')
#     languages, excercises = zip(*exercise_root.items())
#     exercise = exercises[0]
#     if not 'title' in of and not 'name' in of:
#         if len(languages) == 1:
#             l = exercises[0].get('title')
#         else
#             l = { l: exercises[i].get('title') for i, l in enumerate(languages) }
#         of['title'] = l
#     if not 'description' in of:
#         of['description'] = exercise.get('description', '')
#     if 'url' in exercise:
#         of['url'] = exercise['url']
#     else:
#         of['url'] = url_to_exercise(request, course['key'], exercise['key'])
#


# def aplus_json(course):
#     try:
#         with open('course.yaml') as f:
#             _file = yaml.load(f.read())
#             course_to_aplus_json(_file)
#     except:
#         print("Error")
