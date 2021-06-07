import argparse
import numpy as np
import sys

import os
from os import listdir
from os.path import isfile, join

from py3dtiles import B3dm, BatchTable, BoundingVolumeBox, GlTF
from py3dtiles import Tile, TileSet
from Tilers.kd_tree import kd_tree

from geojson import Geojson, Geojsons



def parse_command_line():
    # arg parse
    text = '''A small utility that build a 3DTiles tileset out of the content
               of an geojson repository'''
    parser = argparse.ArgumentParser(description=text)

    # adding positional arguments
    parser.add_argument('--paths',
                        nargs='*',
                        type=str,  
                        help='path to the database configuration file')

    parser.add_argument('--group',
                        nargs='*',
                        type=str,  
                        help='method to merge features together')
    
    parser.add_argument('--properties',
                        nargs='*',
                        type=str,  
                        help='name of the properties to read in Geojson files')

    parser.add_argument('--obj',
                        nargs='*',
                        type=str,  
                        help='create also obj model with specified name')

    result = parser.parse_args()

    if(result.group == None):
        result.group = ['none']

    if(result.obj == None):
        result.obj = ['']
    elif(len(result.obj) == 0):
        result.obj = ['result.obj']
    elif('.obj' not in result.obj[0]):
        result.obj[0] = result.obj[0] + '.obj'

    if(result.properties == None or len(result.properties) % 2 != 0):
        result.properties = ['height','HAUTEUR','z','Z_MAX','prec','PREC_ALTI']
    else:
        if('height' not in result.properties):
            result.properties += ['height','HAUTEUR']
        if('prec' not in result.properties):
            result.properties += ['prec','PREC_ALTI']
        if('z' not in result.properties):
            result.properties += ['z','Z_MAX']

    if(result.paths == None):
        print("Please provide a path to a directory " \
                "containing some geojson files")
        print("Exiting")
        sys.exit(1)

    return result



def create_tile_content(pre_tile):
    """
    :param pre_tile: an array containing features of a single tile

    :return: a B3dm tile.
    """
    #create B3DM content
    arrays = []
    for feature in pre_tile:
        arrays.append({
            'position': feature.geom.getPositionArray(),
            'normal': feature.geom.getNormalArray(),
            'bbox': [[float(i) for i in j] for j in feature.geom.getBbox()]
        })
        
    # GlTF uses a y-up coordinate system whereas the geographical data (stored
    # in the 3DCityDB database) uses a z-up coordinate system convention. In
    # order to comply with Gltf we thus need to realize a z-up to y-up
    # coordinate transform for the data to respect the glTF convention. This
    # rotation gets "corrected" (taken care of) by the B3dm/gltf parser on the
    # client side when using (displaying) the data.
    # Refer to the note concerning the recommended data workflow
    # https://github.com/AnalyticalGraphicsInc/3d-tiles/tree/master/specification#gltf-transforms
    # for more details on this matter.
    transform = np.array([1, 0,  0, 0,
                      0, 0, -1, 0,
                      0, 1,  0, 0,
                      0, 0,  0, 1])  
    gltf = GlTF.from_binary_arrays(arrays, transform)

    # Create a batch table and add the ID of each feature to it
    ids = [feature.get_geojson_id() for feature in pre_tile]
    bt = BatchTable()
    bt.add_property_from_array("id", ids)

    # Eventually wrap the geometries together with the optional
    # BatchTableHierarchy within a B3dm:
    return B3dm.from_glTF(gltf, bt)
        
def from_geojson_directory(path, group, properties, obj_name):    
    """
    :param path: a path to a directory

    :return: a tileset. 
    """
    
    objects = Geojsons.retrieve_geojsons(path,group,properties,obj_name)

    if(len(objects) == 0):
        print("No .geojson found in " + path)
        return None
    else:
        print(str(len(objects)) + " features parsed")
    print(len(Geojsons.base_features))
    # Lump out objects in pre_tiles based on a 2D-Tree technique:
    #pre_tileset = kd_tree(objects,200)
    derived = objects.__class__
    pre_tileset = derived()
    for ob in objects:
        pre_tileset.append([ob])
    #pre_tileset = objects.__class__
    # Get the centroid of the tileset and translate all of the geojson 
    # by this centroid
    # which will be later added in the transform part of each tiles
    centroid = objects.get_centroid()  
    objects.translate_tileset(centroid)       
    
    tileset = TileSet()

    for index, pre_tile in enumerate(pre_tileset):

        tile = Tile()  
        tile.set_geometric_error(50)

        tile_content_b3dm = create_tile_content(pre_tile)
        tile.set_content(tile_content_b3dm)
        tile.set_transform([1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    centroid[0], centroid[1], centroid[2], 1])
        tile.set_refine_mode('REPLACE')
        bounding_box = BoundingVolumeBox()        
        for geojson in pre_tile:
            bounding_box.add(geojson.get_bounding_volume_box()) 
        tile.set_bounding_volume(bounding_box)

        child = Tile()
        child.set_geometric_error(50)
        child_features = [Geojsons.base_features[i] for i in Geojsons.features_dict[index]]
        gjs = Geojsons(child_features)
        c_derived = objects.__class__
        child_pre_tile = c_derived()
        for gj in gjs:
            child_pre_tile.append(gj)
        gjs.translate_tileset(centroid)
        child_content_b3dm = create_tile_content(child_pre_tile)
        child.set_content(child_content_b3dm)
        child.set_transform([1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1])
        child.set_refine_mode('REPLACE')
        bounding_box = BoundingVolumeBox()        
        for geojson in child_pre_tile:
            bounding_box.add(geojson.get_bounding_volume_box()) 
        child.set_bounding_volume(bounding_box)
        tile.add_child(child)

        tileset.add_tile(tile)

    return tileset

def main():
    """
    :return: no return value

    this function creates either :
    - a repository named "geojson_tileset" where the
    tileset is stored if the directory does only contains geojson files.
    - or a repository named "geojson_tilesets" that contains all tilesets are stored
    created from sub_directories 
    and a classes.txt that contains the name of all tilesets
    """
    args = parse_command_line()   
    path = args.paths[0]
    obj_name = args.obj[0]
    if(os.path.isdir(path)):
            print("Writing " + path )
            tileset = from_geojson_directory(path,args.group,args.properties,obj_name)
            if(tileset != None):
                tileset.get_root_tile().set_bounding_volume(BoundingVolumeBox())
                folder_name = path.split('/')[-1]
                print("tilset in geojson_tilesets/" + folder_name)
                tileset.write_to_directory("geojson_tilesets/" + folder_name)

if __name__ == '__main__':
    main()
