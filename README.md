# FLATEHR
![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)
[![CI](https://github.com/crs4/flatehr/actions/workflows/main.yaml/badge.svg)](https://github.com/crs4/flatehr/actions/workflows/main.yaml)
![test](https://github.com/crs4/flatehr/raw/master/docs/reports/tests-badge.svg)
![coverage](https://github.com/crs4/flatehr/raw/master/docs/reports/coverage-badge.svg)
![flake8](https://github.com/crs4/flatehr/raw/master/docs/reports/flake8-badge.svg)

**FLATEHR** is a *low-code* Python tool for creating [openEHR](https://www.openehr.org/) **compositions** from different kind of sources. At the moment, **xml** and **json** sources are supported.
Generated compositions are formatted according to the [flat (simSDT) format](https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html). 


**TL;DR:** it allows to populate compositions mapping key-values generated from a source (for example a XPATH and its relative values from an xml file) to simSDT paths. 
The mapping is configured via a **yaml** file.
See the [examples section](#Examples) for more details.

## Architecture
![architecture](https://github.com/crs4/flatehr/raw/master/docs/architecture.png)
FLATEHR extracts an **ordered list of key-value tuples** from a source according to a [configuration file](#configuration). 
Keys are identified by XPATH or [JSONPATH](https://github.com/h2non/jsonpath-ng) strings, depending on the type of the source.
A **flat composition** and optionally an **external ehr id** are then generated according to the configured mappings, 
and can be submitted to an openEHR server suppporting the simSDT syntax.

## Features
 * N:N mappings between source keys and flat paths
 * source keys order preserved, helpful for properly managed multiple cardinality RM objects
 * render values using jinja templates
 * use a value map to converts the source values
 * retrieve values from the web template using jq
 * set null flavour when some mapping is missing
 * set missing required values to the default value (defined in the web template)
 * automatic configuration skeleton generation
 * inspect a template

## Installation
Dependencies:
 * [Poetry](https://python-poetry.org/): ```pip install poetry```

 For installing FLATEHR, first enable virtualenv:

```
$ poetry shell
```

Then run:

```
$ make install
```

## Configuration

The configuration for generating a composition (see [this](#generating-a-configuration-file) 
and [this](#generating-a-composition)) is written in YAML file.
For a quick overview, take a look at the [examples section](#examples).

Here is the supported syntax:

* [paths](#paths)
* [paths.\<path\>](#paths.\<path\>)
* [paths.\<path\>.maps_to](#paths.\<path\>.maps_to)
* [paths.\<path\>.suffixes](#paths.\<path\>.suffixes)
* [paths.\<path\>.suffixes.\<suffix\>](#paths.\<path\>.suffixes.\<suffix\>)
* [paths.\<path\>.suffixes.\<suffix\>.value](#paths.\<path\>.suffixes.\<suffix\>.value)
* [paths.\<path\>.suffixes.\<suffix\>.jq](#paths.\<path\>.suffixes.\<suffix\>.jq)
* [paths.\<path\>.value_map](#paths.\<path\>.value_map)
* [paths.\<path\>.null_flavor](#paths.\<path\>.null_flavor)
* [set_missing_required_to_default](#set_missing_required_to_default)
* [ehr_id](#ehr_id)
* [ehr_id.maps_to](#ehr_id.maps_to)
* [ehr_id.value](#ehr_id.value)

#### paths
---
The set of simSDT paths to be mapped.

#### paths.\<path\>
---
A valid simSDT path.
For example:
```
paths:
  test/patient_data/gender/biological_sex:
```

Ctx paths can be used too:

```
paths:
  ctx/language:
```

Values can be a string (static mapping) or an object (dynamic mapping, see [suffixes](#paths.\<path\>.suffixes.\<suffix\>)):

```
paths:
  ctx/language: en
```

Multiple cardinality RM objects can be mapped, so that they are increased 
each time the source key appears (only one maps_to is possible in this case)

```
paths:
  test/histopathology/result_group/laboratory_test_result/any_event:
    maps_to:
      - "$..Event[?(@.@eventtype == 'Histopathology')]"

```

It is also possible to set all the children paths to a multiple cardinality object.
In this case no maps_to can be set.
```
paths:
  test/histopathology/result_group/laboratory_test_result/any_event:*/test_name:
    maps_to: []
    suffixes:
      "": "Histopathology"

```



#### paths.\<path\>.maps_to
---
List of source keys that the given path maps to. It can be empty.
```
paths:
  test/patient_data/gender/biological_sex:
    maps_to: 
     - "$..Dataelement_85_1.'#text'"

```
For XPath, you can use *ns* as placeholder for the namespace, as in *//ns:Dataelement_3_1/text()*

#### paths.\<path\>.suffixes
---
Suffixes to append to the given path.

```
paths:
  test/patient_data/gender/biological_sex:
    maps_to: 
     - "$..Dataelement_85_1.'#text'"
    suffixes:
      "|value" : "a valid value" 
```


#### paths.\<path\>.suffixes.\<suffix\>
---

A valid suffix to append to the given path, usually something like ```|code```. 
If not suffix is expected, an empty string ("") can be used.
The value is a jinja template where some objects and methods are available,
in particular  *maps_to* and *value_map*. 
Suffix can be also and object, see [value](#paths.\<path\>.suffixes.\<suffix\>.value)
and [jq](#paths.\<path\>.suffixes.\<suffix\>.jq) .

```
paths:
  ctx/territory:
    maps_to:
      - "$..Location.@name"
    suffixes:
      "|code": "{{ value_map[maps_to[0]]  }}"
      "|terminology" : "ISO_3166-1"
    value_map: # you can define a value_map that is available in the suffixes
      test: IT
      le test: FR

```

#### paths.\<path\>.suffixes.\<suffix\>.value
---
The value (jinja template, see [here](#paths.\<path\>.suffixes.\<suffix\>))
for the given suffix.

#### paths.\<path\>.suffixes.\<suffix\>.jq
---
Boolean, if true the [suffix value](#paths.\<path\>.suffixes.\<suffix\>.value) is 
used as parameter to *jq* (the input is the relative web template json for the given path).
Useful for retrieving values from the template and use them for assigning the suffix.

```

paths:
  test/patient_data/gender/biological_sex:
    maps_to: #list of source key maps expressed as jsonpath
     - "$..Dataelement_85_1.'#text'"
    suffixes:
      "|code":
        value: '.inputs[0].list[] | select (.label == "{{ maps_to[0] | upper }}") | .value'
        jq: true 

```

#### paths.\<path\>.value_map
---
Custom value mapping that can be used for the suffixes values 
(available in the jinja template rendering).
```
paths:
  ctx/territory:
    maps_to:
      - "$..Location.@name"
    suffixes:
      "|code": "{{ value_map[maps_to[0]]  }}"
      "|terminology" : "ISO_3166-1"
    value_map:
      test: IT
      le test: FR
```

#### paths.\<path\>.null_flavor
---
If set and some *maps_to* key is missing, the given null flavor is used for the path.

```
paths:
  test/patient_data/gender/biological_sex:
    maps_to:
     - "$..Dataelement_85_1.'#text'"
    null_flavor:
      value: unknown
      code: 253
      terminology: openehr

```

#### set_missing_required_to_default
---
Boolean, if set to true all the missing paths (after processing the source keys)
that are required are set to their default value (if specified in the template).

#### ehr_id
-----
It allows to specify the ehr id (external ref) for the composition.

```
ehr_id:
  maps_to: []
  value : "{{ random_ehr_id() }}"
```

#### ehr_id.maps_to
-------------------

See [here](#paths.\<path\>.maps_to)

#### ehr_id.value
-------------------
A jinja template, similiar to suffixes. A random_ehr_id function is available.

## CLI
Main command:

```
$ flatehr -h
usage: flatehr [-h] [--version] {generate,inspect} ...

positional arguments:
  {generate,inspect}
    inspect           Shows the template tree, with info about type, cardinality,
                      requiredness and optionally aql path and expected inputs.

optional arguments:
  -h, --help          show this help message and exit
  --version           show program's version number and exit

```

### Generating a Configuration File

For generating the configuration skeleton from a template, run:
```
$ flatehr generate skeleton -h
usage: flatehr generate skeleton [-h] template_file

Generate a configuration skeleton for the given template.

positional arguments:
  template_file  the path to the web template (json)

optional arguments:
  -h, --help     show this help message and exit

```

### Generating a Composition

For generating a composition, use this subcommand:
```
$ flatehr generate from-file -h
usage: flatehr generate from-file [-h] -t TEMPLATE_FILE -c CONF_FILE [-r RELATIVE_ROOT] [-s | --skip-ehr-id | --no-skip-ehr-id] input_file

Generates composition(s) from a file. xml and json sources supported.
Prints on stdout an external ehr id (if flag --skip-ehr-id is not set) and the flat composition.
If --relative-root is set, as many compositions are generated as keys with the given value exists in the source.

positional arguments:
  input_file            source file

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATE_FILE, --template-file TEMPLATE_FILE
                        web template path
  -c CONF_FILE, --conf-file CONF_FILE
                        yaml configuration path
  -r RELATIVE_ROOT, --relative-root RELATIVE_ROOT
                        id for the root(s) that maps 1:1 to composition
                        (default: None)
  -s, --skip-ehr-id, --no-skip-ehr-id
                        if set, ehr_id is not printed
                        (default: False)

```

For an example, try:
```bash
$ flatehr generate from-file -t tests/resources/web_template.json -c tests/resources/xml_conf.yaml --skip-ehr-id tests/resources/source.xml
```

### Inspecting a template

For inspecting a template, run:
```
$ flatehr inspect -h
usage: flatehr inspect [-h] [-a | --aql-path | --no-aql-path] [-i | --inputs | --no-inputs] template_file

Shows the template tree, with info about type, cardinality,
requiredness and optionally aql path and expected inputs.

positional arguments:
  template_file         path to the web template (json)

optional arguments:
  -h, --help            show this help message and exit
  -a, --aql-path, --no-aql-path
                        flag, if true shows the aql path for each node
                        (default: False)
  -i, --inputs, --no-inputs
                        flag, if true shows the inputs for each node
                        (default: False)

```



## Examples
Here is an excerpt from *tests/resources/json_conf.yaml*. It maps the source *tests/resources/source.json* to a composition defined by the template *tests/resources/web_template.json* (see also *template.opt* and *template.zip* in the same directory) 
It uses the jsonpath syntax adopted by [jsonpath-ng](https://github.com/h2non/jsonpath-ng) library.

```yaml
paths:
  test/patient_data/gender/biological_sex: # destination path (completed by the suffixes below)
    maps_to: #list of source key maps expressed as jsonpath
     - "$..Dataelement_85_1.'#text'"
    suffixes:
      "|value" : "{{ maps_to[0] | upper }}" # suffixes are rendered as jinja templates, `maps_to` are available
      "|code":
        value: '.inputs[0].list[] | select (.label == "{{ maps_to[0] | upper }}") | .value'
        jq: true # if jq is true, the rendered value is passed as argument jq. The json input is the relative web template
      "|terminology" :
        value: '.inputs[0].terminology'
        jq: true
    null_flavor: # if not all `maps_to` are available, null flavour can be used
      value: unknown
      code: 253
      terminology: openehr

  ctx/language: en #for static value it is as simple as that

  ctx/territory:
    maps_to:
      - "$..Location.@name"
    suffixes:
      "|code": "{{ value_map[maps_to[0]]  }}"
      "|terminology" : "ISO_3166-1"
    value_map: # you can define a value_map that is available in the suffixes
      test: IT
      le test: FR

  test/histopathology/result_group/laboratory_test_result/any_event: #non leaf path with multiple cardinality can be mapped, they are increased when mapping occurs
    maps_to:
      - "$..Event[?(@.@eventtype == 'Histopathology')]"


```

For more exaustive examples, see *tests/test_cli.sh*.


## Ingesting
From parallel ingesting multiple sources to an openEHR istance, take a look at *scripts/ingest.sh*.





