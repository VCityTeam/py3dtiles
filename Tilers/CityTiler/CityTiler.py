import argparse
import numpy as np

from py3dtiles import B3dm, BatchTable, BoundingVolumeBox, GlTF
from py3dtiles import Tile, TileSet

from building import Building, Buildings
from kd_tree import kd_tree
from database_accesses import open_data_base, retrieve_geometries, create_batch_table_hierachy


def ParseCommandLine():
    # arg parse
    descr = '''A small utility that build a 3DTiles tileset out of the content
               of a 3DCityDB database.'''
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('db_config_path',
                        nargs='?',
                        default='CityTilerDBConfig.yml',
                        type=str,
                        help='Path to the database configuration file')
    parser.add_argument('--with_BTH',
                        dest='with_BTH',
                        action='store_true',
                        help='Adds a Batch Table Hierachy when defined')
    return parser.parse_args()


def create_tile_content(cursor, buildingIds, offset, args):
    """
    :param offset: the offset (a a 3D "vector" of floats) by which the
                   geographical coordinates should be translated (the
                   computation is done at the GIS level)
    :type args: CLI arguments as obtained with an ArgumentParser. Used to
                determine whether to define attach an optional
                BatchTable or possibly a BatchTableHierachy
    :rtype: a TileContent in the form a B3dm.
    """
    arrays = retrieve_geometries(cursor, buildingIds, offset)

    # GlTF uses a y-up coordinate system whereas the geographical data (stored
    # in the 3DCityDB database) uses a z-up coordinate system convention. In
    # order to comply with Gltf we thus need to realize a z-up to y-up
    # coordinate transform for the data to respect the glTF convention. This
    # rotation gets "corrected" (taken care of) by the B3dm/gltf parser on the
    # client side when using (displaying) the data.
    # Refer to the note concerning the recommended data workflow
    #    https://github.com/AnalyticalGraphicsInc/3d-tiles/tree/master/specification#gltf-transforms
    # for more details on this matter.
    transform = np.array([1, 0,  0, 0,
                          0, 0, -1, 0,
                          0, 1,  0, 0,
                          0, 0,  0, 1])
    gltf = GlTF.from_binary_arrays(arrays, transform)

    # When required attach a BatchTable with its optional extensions
    if args.with_BTH:
        bth = create_batch_table_hierachy(cursor, buildingIds, args)
        bt = BatchTable()
        bt.add_extension(bth)
    else:
        bt = None

    # Eventually wrap the geometries together with the optional
    # BatchTableHierarchy within a B3dm:
    return B3dm.from_glTF(gltf, bt)


def from_3dcitydb(cursor, args):
    """
    :type args: CLI arguments as obtained with an ArgumentParser.
    """

    # Retrieve all the buildings encountered in the 3DCityDB database together
    # with their 3D bounding box.
    cursor.execute("SELECT building.id, BOX3D(cityobject.envelope) "
        "FROM building JOIN cityobject ON building.id=cityobject.id "
        "WHERE building.id=building.building_root_id")
    buildings = Buildings()
    for t in cursor.fetchall():
        id = t[0]
        box = t[1]
        buildings.append(Building(id, box))

    # Lump out buildings in pre_tiles based on a 2D-Tree technique:
    pre_tiles = kd_tree(buildings, 20)

    tileset = TileSet()
    for tile_buildings in pre_tiles:
        tile = Tile()
        tile.set_geometric_error(500)

        # Construct the tile content and attach it to the new Tile:
        ids = tuple([building.getId() for building in tile_buildings])
        centroid = tile_buildings.getCentroid()
        tile_content_b3dm = create_tile_content(cursor, ids, centroid, args)
        tile.set_content(tile_content_b3dm)

        # The current new tile bounding volume shall be a box enclosing the
        # buildings withheld in the considered tile_buildings:
        bounding_box = BoundingVolumeBox()
        for building in tile_buildings:
            bounding_box.add(building.getBoundingVolumeBox())

        # The Tile Content returned by the above call to create_tile_content()
        # (refer to the usage of the centroid/offset third argument) uses
        # coordinates that are local to the centroid (considered as a
        # referential system within the chosen geographical coordinate system).
        # Yet the above computed bounding_box was set up based on
        # coordinates that are relative to the chosen geographical coordinate
        # system. We thus need to align the Tile Content to the
        # BoundingVolumeBox of the Tile by "adjusting" to this change of
        # referential:
        bounding_box.translate([- centroid[i] for i in range(0,3)])
        tile.set_bounding_volume(bounding_box)

        # The transformation matrix for the tile is limited to a translation
        # to the centroid (refer to the offset realized by the
        # create_tile_content() method).
        # Note: the geographical data (stored in the 3DCityDB) uses a z-up
        #       referential convention. When building the B3dm/gltf, and in
        #       order to comply to the y-up gltf convention) it was necessary
        #       (look for the definition of the `transform` matrix when invoking
        #       `GlTF.from_binary_arrays(arrays, transform)` in the
        #        create_tile_content() method) to realize a z-up to y-up
        #        coordinate transform. The Tile is not aware on this z-to-y
        #        rotation (when writing the data) followed by the invert y-to-z
        #        rotation (when reading the data) that only concerns the gltf
        #        part of the TileContent.
        tile.set_transform([1, 0, 0, 0,
                            0, 1, 0, 0,
                            0, 0, 1, 0,
                           centroid[0], centroid[1], centroid[2], 1])

        # Eventually we can add the newly build tile to the tile set:
        tileset.add_tile(tile)

    # Note: we don't need to explicitly adapt the TileSet's root tile
    # bounding volume, because TileSet::write_to_directory() already
    # takes care of this synchronisation.

    # A shallow attempt at providing some traceability on where the resulting
    # data set comes from:
    cursor.execute('SELECT inet_client_addr()')
    server_ip = cursor.fetchone()[0]
    cursor.execute('SELECT current_database()')
    database_name = cursor.fetchone()[0]
    origin  = f'This tileset is the result of Py3DTiles {__file__} script '
    origin += f'run with data extracted from database {database_name} '
    origin += f' obtained from server {server_ip}.'
    tileset.add_asset_extras(origin)

    return tileset


if __name__ == '__main__':
    args = ParseCommandLine()
    cursor = open_data_base(args)
    tileset = from_3dcitydb(cursor, args)
    cursor.close()
    tileset.write_to_directory('junk')
