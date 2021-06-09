# -*- coding: utf-8 -*-
import os
import sys
import json
import jsonschema
import pathlib

from .threedtiles_core_schemas import ThreeDTilesCoreSchemas
from .batch_table_hierarchy_extension_schemas import BatchTableHierarchySchemas
from .temporal_extension_schemas import TemporalExtensionSchemas

class SchemaValidators:
    """
    Dictionary holding the set of validated schemas. The dictionary key is
    the name of the schema as encountered in the "title" property of the schema.
    """
    schemas = None
    """
    Dictionary with the class_names (i.e. the name of the classes inheriting
    from ThreeDTilesNotion) as key and the "title" property of the associated
    schema as value. class_names can be seen as (technical) syntactic sugar
    over the true schema identifier that is the "title".
    """
    class_names = None
    """
    Resolver is a technical mean for retrieving any possible sub-schema 
    indicated within a given schema through a $ref entry.
    """
    resolver = None

    def __init__(self):
        if not self.schemas:
            self.schemas = dict()
            self.class_names = dict()

            # They are two contexts of usage for this constructor that must
            # set up the directory where all the schema files are located:
            #  - a package developing stage where the directory is a relative 
            #    path (within the directory layout of the sources)
            #  - a package post-installation stage where the directory is 
            #    absolute because it is relative to the python's directory 
            #    path of its installed packages (that would the absolute 
            #    sys.prefix directory path, if they where no python-eggs and
            #    other advanced package features).
            # 
            # The relative directory context directory (when working within the
            # source tree):
            schema_directory = 'py3dtiles/jsonschemas'
            if not os.path.isdir(schema_directory):
                # We had no success in relative context. Could this be an 
                # absolute path context ?
                installed_path=pathlib.Path(__file__).parent.absolute()
                schema_directory = os.path.join(installed_path, "jsonschemas")
                if not os.path.isdir(schema_directory):
                    print('Failed to establish an installed package context:')
                    print(f'unfound directory path {schema_directory}')
                    print('Exiting.')
                    sys.exit(1)

            # sub-schemas within the same directory (provided as absolute path)
            # as the given schema. Refer to
            #     https://github.com/Julian/jsonschema/issues/98
            # for the reasons of the following parameters and call
            base_uri = pathlib.Path(os.path.abspath(schema_directory)).as_uri() + '/'
            self.resolver = jsonschema.RefResolver(base_uri, None)

            self.register_schema_with_sample_list(ThreeDTilesCoreSchemas())
            self.register_schema_with_sample_list(BatchTableHierarchySchemas())
            self.register_schema_with_sample_list(TemporalExtensionSchemas())

    def register_schema_with_sample_list(self, schema_with_sample_list):
        for schema_with_sample in schema_with_sample_list:
            self.register_schema_with_sample(schema_with_sample)

    def register_schema_with_sample(self, schema_with_sample):
        file_name = schema_with_sample.get_schema_file_path()
        if not os.path.isfile(file_name):
            print(f'No such file as {file_name}')
            sys.exit(1)

        try:
            with open(file_name, 'r') as schema_file:
                schema = json.loads(schema_file.read())
        except:
            print(f'Unable to parse schema held in {file_name}')
            sys.exit(1)

        try:
            title = schema['title']
        except:
            print('Schema argument misses a title. Dropping extension.')
            sys.exit(1)

        key = schema_with_sample.get_key()
        if title in self.schemas:
            if not key in 'BoundingVolume':
                # This is a legitimate case where some classes share the
                # same validator
                pass
            else:
                print(f'Class {key} already has schema named {title}.')
                sys.exit(1)
        else:
            validator = jsonschema.Draft7Validator(schema, resolver = self.resolver)

            try:
                # Strangely enough, in order to validate the schema itself, we
                # do need to provide a sample complying with the json format:
                validator.validate(schema_with_sample.get_sample())
            except jsonschema.exceptions.SchemaError:
                print(f'Invalid schema {title}')
                sys.exit(1)
            self.schemas[title] = {'schema': schema, 'validator': validator}
        self.class_names[key] = title

    def get_validator(self, class_name_key):
        if not class_name_key in self.class_names:
            print(f'Unregistered schema (class) key {class_name_key}')
            return None
        title = self.class_names[class_name_key]
        if not title in self.schemas:
            print(f'Unregistered schema with title {title}')
            return None
        try:
            return self.schemas[title]["validator"]
        except:
            print(f'Cannot find validator for schema {class_name_key}')
        return None

    def __contains__(self, schema_name):
        if schema_name in self.schemas:
            return True
        return False
