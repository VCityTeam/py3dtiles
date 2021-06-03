import unittest
import os
from py3dtiles import BoundingVolumeBox
import filecmp

from Tilers.GeojsonTiler.GeojsonTiler import from_geojson_directory

class Test_Tile(unittest.TestCase):

    def test_basic_case(self):
        path = 'tests/geojson_tiler_test_data/geojson_1/'
        obj_name = 'tests/geojson_tiler_test_data/generated_objs/block.obj'
        group = ['none']
        properties = ['height','HAUTEUR','prec','PREC_ALTI','z','Z_MAX']

        if not os.path.exists('tests/geojson_tiler_test_data/generated_objs'):
            os.makedirs('tests/geojson_tiler_test_data/generated_objs')
        if not os.path.exists('tests/geojson_tiler_test_data/generated_tilesets'):
            os.makedirs('tests/geojson_tiler_test_data/generated_tilesets')

        tileset = from_geojson_directory(path,group,properties,obj_name)
        if(tileset != None):
            tileset.get_root_tile().set_bounding_volume(BoundingVolumeBox())
            folder_name = "basic_case"
            print("tileset in tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
            tileset.write_to_directory("tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
        assert filecmp.cmp(obj_name, 'tests/geojson_tiler_test_data/expected_objs/block.obj')

    def test_properties_with_other_name(self):
        path = 'tests/geojson_tiler_test_data/geojson_2/'
        obj_name = 'tests/geojson_tiler_test_data/generated_objs/block_other_properties_name.obj'
        group = ['none']
        properties = ['height','HEIGHT','prec','NONE','z','Z']

        if not os.path.exists('tests/geojson_tiler_test_data/generated_objs'):
            os.makedirs('tests/geojson_tiler_test_data/generated_objs')
        if not os.path.exists('tests/geojson_tiler_test_data/generated_tilesets'):
            os.makedirs('tests/geojson_tiler_test_data/generated_tilesets')

        tileset = from_geojson_directory(path,group,properties,obj_name)
        if(tileset != None):
            tileset.get_root_tile().set_bounding_volume(BoundingVolumeBox())
            folder_name = "properties_with_other_name"
            print("tileset in tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
            tileset.write_to_directory("tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
        assert filecmp.cmp(obj_name, 'tests/geojson_tiler_test_data/expected_objs/block_other_properties_name.obj')

    def test_group_cube_100(self):
        path = 'tests/geojson_tiler_test_data/geojson_1/'
        obj_name = 'tests/geojson_tiler_test_data/generated_objs/block_group_by_cube_100.obj'
        group = ['cube','100']
        properties = ['height','HAUTEUR','prec','PREC_ALTI','z','Z_MAX']

        if not os.path.exists('tests/geojson_tiler_test_data/generated_objs'):
            os.makedirs('tests/geojson_tiler_test_data/generated_objs')
        if not os.path.exists('tests/geojson_tiler_test_data/generated_tilesets'):
            os.makedirs('tests/geojson_tiler_test_data/generated_tilesets')

        tileset = from_geojson_directory(path,group,properties,obj_name)
        if(tileset != None):
            tileset.get_root_tile().set_bounding_volume(BoundingVolumeBox())
            folder_name = "group_cube_100"
            print("tileset in tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
            tileset.write_to_directory("tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
        assert filecmp.cmp(obj_name, 'tests/geojson_tiler_test_data/expected_objs/block_group_by_cube_100.obj')
    
    def test_group_road(self):
        path = 'tests/geojson_tiler_test_data/geojson_1/'
        obj_name = 'tests/geojson_tiler_test_data/generated_objs/block_group_by_roads.obj'
        group = ['road']
        properties = ['height','HAUTEUR','prec','PREC_ALTI','z','Z_MAX']

        if not os.path.exists('tests/geojson_tiler_test_data/generated_objs'):
            os.makedirs('tests/geojson_tiler_test_data/generated_objs')
        if not os.path.exists('tests/geojson_tiler_test_data/generated_tilesets'):
            os.makedirs('tests/geojson_tiler_test_data/generated_tilesets')
            
        tileset = from_geojson_directory(path,group,properties,obj_name)
        if(tileset != None):
            tileset.get_root_tile().set_bounding_volume(BoundingVolumeBox())
            folder_name = "group_roads"
            print("tileset in tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
            tileset.write_to_directory("tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
        assert filecmp.cmp(obj_name, 'tests/geojson_tiler_test_data/expected_objs/block_group_by_roads.obj')

    def test_group_polygons(self):
        path = 'tests/geojson_tiler_test_data/geojson_1/'
        obj_name = 'tests/geojson_tiler_test_data/generated_objs/block_group_by_polygons.obj'
        group = ['polygon']
        properties = ['height','HAUTEUR','prec','PREC_ALTI','z','Z_MAX']

        if not os.path.exists('tests/geojson_tiler_test_data/generated_objs'):
            os.makedirs('tests/geojson_tiler_test_data/generated_objs')
        if not os.path.exists('tests/geojson_tiler_test_data/generated_tilesets'):
            os.makedirs('tests/geojson_tiler_test_data/generated_tilesets')
            
        tileset = from_geojson_directory(path,group,properties,obj_name)
        if(tileset != None):
            tileset.get_root_tile().set_bounding_volume(BoundingVolumeBox())
            folder_name = "group_roads"
            print("tileset in tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
            tileset.write_to_directory("tests/geojson_tiler_test_data/generated_tilesets/" + folder_name)
        assert filecmp.cmp(obj_name, 'tests/geojson_tiler_test_data/expected_objs/block_group_by_polygons.obj')        

if __name__ == '__main__':
    unittest.main()