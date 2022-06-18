"""
Author: Chandler Ross
Date: 5/20/2022
Notes:
    Module to have a few simple convolution filters for raster images
"""


#Import helpful modules
import os, sys, rasterio
import numpy as np
try:
    from osgeo import gdal
    from osgeo import gdalconst
except ImportError as e:
    print(e)
    import gdal
    import gdalconst

#=======================================================================================================================
#                   Helper Function(s)
#=======================================================================================================================

def delete_svis(temp_folder):
    #delete the temporary SVI files in the temp folder
    for i in os.listdir(temp_folder):
        try:
            del_path = temp_folder + i
            os.remove(del_path)
        except OSError as e:
            print("Error: %s : %s" % (i, e.strerror))

def create_raster(file_list, file_out):
    """

    :return: A raster that combines all of the added rasters
    """

    #looks like I will have to make a temp folder with the SVIs then add them all to a new raster then delete
    #   the temp SVIs

    #write the SVI as a band with rasterio
    #https://gis.stackexchange.com/questions/223910/using-rasterio-or-gdal-to-stack-multiple-bands-without-using-subprocess-commands
    #https://gis.stackexchange.com/questions/49706/adding-band-to-existing-geotiff-using-gdal

    #empyt list of the files
    #file_list = []

    # print('create raster list: ', file_list)

    # Read metadata of first file
    with rasterio.open(file_list[0]) as src0:
        meta = src0.meta

    # Update meta to reflect the number of layers
    meta.update(count = len(file_list))

    # Read each layer and write it to stack
    with rasterio.open(file_out, 'w', **meta) as dst:
        for id, layer in enumerate(file_list, start=1):
            with rasterio.open(layer) as src1:
                dst.write_band(id, src1.read(1))


def gdal_type_number_locator(type):
    """
    Finds the integer for the raster type
    :param type: string, ex: Float64
    :return: An integer that corresponnds with the GDAL raster type, helps for creating a new GDAL raster dataset from
    an existing one
    """
    if(type=='Float32'):
        return gdal.GDT_Float32
    elif(type=='Float64'):
        return gdal.GDT_Float64
    elif(type=='Unknown'):
        return gdal.GDT_Unknown
    elif(type=='Byte'):
        return gdal.GDT_Byte
    elif(type=='UInt16'):
        return gdal.GDT_UInt16
    elif(type=='Int16'):
        return gdal.GDT_Int16
    elif(type=='UInt32'):
        return gdal.GDT_UInt32
    elif(type=='Int32'):
        return gdal.GDT_Int32
    elif(type=='UInt64'):
        return gdal.GDT_UInt64
    elif(type=='Int64'):
        return gdal.GDT_Int64
    elif(type=='CInt16'):
        return gdal.GDT_CInt16
    elif(type=='CInt32'):
        return gdal.GDT_CInt32
    elif(type=='CFloat32'):
        return gdal.GDT_CFloat32
    elif(type=='CFloat64'):
        return gdal.GDT_CFloat64
    else:
        print('Incorrect String or raster type entered \nTry: Unknown, Byte, UInt16, Int16, UInt32, Int32, UInt64, Int64, '
              'Float32, Float64, CInt16, CInt32, CFloat32, or CFloat64')
        return None



"""
GDAL Merge Information
where the script lives
C:/Users/cross8046/Anaconda3/envs/thesis/Scripts
how to use it in python https://gis.stackexchange.com/questions/236746/calling-gdal-merge-into-python-script


"""

#=======================================================================================================================
#                   Filters
#=======================================================================================================================

# 3x3 laplacian 4 filter
def edge_detect_3x3(in_path, out_path, band_index=None, driver_type='GTiff'):
    #set the driver
    driver = gdal.GetDriverByName(driver_type)
    driver.Register()
    #turn the raster file into a gdal dataset
    dataset_sub = gdal.Open(in_path, gdalconst.GA_ReadOnly)

    #get information about the dataset
    rows = dataset_sub.RasterYSize
    cols = dataset_sub.RasterXSize
    band_num = dataset_sub.RasterCount
    projection = dataset_sub.GetProjection()
    metadata = dataset_sub.GetMetadata()
    geotransform = dataset_sub.GetGeoTransform()
    laplacian_4_array = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])

    #if statement that determines of one band is run or all of the bands are run
    if(band_index==None):
        pass
    else:
        # Get the specified band
        band = dataset_sub.GetRasterBand(band_index)
        #get the band type, helps with formatting the output band type
        band_type = gdal.GetDataTypeName(band.DataType)

        # Make the output image data to write to
        # The output bands
        ds_out = driver.Create(out_path, cols, rows, 1, band_type)
        band_out = ds_out.GetRasterBand(1)
        band_type_out = gdal.GetDataTypeName(band_out.DataType)

        #set the output array
        array_out = np.zeros([rows, cols])

        # read by block
        block_size_x = 3
        block_size_y = 3

        #Nested for loop that doesnt touch the edges
        #the edge values are set to zero
        for y in range(2, rows):
            for x in range(2, cols):
                data_sub = band.ReadAsArray(x, y, block_size_x, block_size_y)
                # multiply the kernel by the laplacian filter, and the sum becomes the middle number
                #The data_sub has some none values so this is how I am dealing with it
                if data_sub is None:
                    output_val = -9999
                else:
                    arr_mult = np.multiply(laplacian_4_array, data_sub)
                    output_val = np.sum(arr_mult)
                #write this middle value to the new raster
                array_out[x, y] = output_val

        #write the data to the array
        band_out.WriteArray(output_array, 0, 0)
        #set to none to save memory
        band_out = None
        band = None
        ds = None
        ds_out = None


# custom size and filter
def custom_filter(in_file, out_file, square_array, tmp_folder='c:/tmp/', driver_type='GTiff', band_index=None):
    """
    Apply a custom filter to a raster. Works for a multiband raster or a single band.
    :param in_file: input file path; string
    :param out_file: output file path; string
    :param square_array: numpy array with equal length and width; numpy array
    :param driver_type: the gdal driver used for the input/output file type, default for .tif file; string
    :param band_index: default (None) will run for entire multi-band image, can specify a band index; integer
    :return: a filtered raster written to the specified file path
    """

    #set the driver and register it
    driver = gdal.GetDriverByName(driver_type)
    driver.Register()

    # Read in information about the input file
    # Turn the raster file into a gdal dataset
    ds = gdal.Open(in_file, gdalconst.GA_ReadOnly)

    bnd = ds.GetRasterBand(1)

    #get information about the dataset
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    band_num = ds.RasterCount
    projection = ds.GetProjection()
    metadata = ds.GetMetadata()
    geotransform = ds.GetGeoTransform()

    #read in information about the input array
    filter_row_size, filter_column_size = np.shape(square_array)

    #if statement that determines of one band is run or all of the bands are run
    if(band_index==None):

        #empty list for the single band files
        temp_band_list = []

        #for loop to get the band information
        for i in range(band_num):
            # Get the specified band
            band_iteration = i+1
            band = ds.GetRasterBand(band_iteration)
            #get the band type, helps with formatting the output band type
            band_type = gdal.GetDataTypeName(band.DataType)

            band_type_num = gdal_type_number_locator(band_type)

            # Make a temporary file for each band to make into a multi-band raster later
            tmp_file_name = 'tmp_band_' + str(i+1) + in_file[-4:]
            tmp_out_file = os.path.join(tmp_folder, tmp_file_name)

            # Create information about the temporary single band output file
            ds_out = driver.Create(tmp_out_file, cols, rows, band_num, band_type_num)
            # Set the geotransform
            ds_out.SetGeoTransform(geotransform)
            # Set the projection
            ds_out.SetProjection(projection)
            band_out = ds_out.GetRasterBand(1)
            band_type_out = gdal.GetDataTypeName(band_out.DataType)

            # set the output array
            output_array = np.zeros([rows, cols])

            # read by block
            block_size_x = filter_column_size
            block_size_y = filter_row_size

            #ensure the edges are to remain at zero (this should be changed later by duplicating the data for the edges)
            y_edge_val = block_size_y - 1
            x_edge_val = block_size_x - 1

            # Nested for loop that doesnt touch the edges
            for y in range(y_edge_val, rows-y_edge_val):
                for x in range(x_edge_val, cols-x_edge_val):
                    data_sub = band.ReadAsArray(x, y, block_size_x, block_size_y)
                    # multiply the kernel by the custom filter, and the sum becomes the middle number
                    #The data_sub has some none values so this is how I am dealing with it
                    if data_sub is None:
                        output_val = -9999
                    else:
                        arr_mult = np.multiply(square_array, data_sub)
                        output_val = np.sum(arr_mult)
                    #write this middle value to the new raster
                    output_array[y, x] = output_val

            #write the data to the array
            band_out.WriteArray(output_array, 0, 0)

            #append the file to the list
            temp_band_list.append(tmp_out_file)

            #set to none to save memory
            band_out = None
            band = None
            ds = None
            ds_out = None

        #take the list of single bands and make a multiband raster
        create_raster(temp_band_list, out_file)

        # Delete the temporary single band indices files
        delete_svis(tmp_folder)

    else:
        # Get the specified band
        band = ds.GetRasterBand(band_index)
        #get the band type, helps with formatting the output band type
        band_type = gdal.GetDataTypeName(band.DataType)

        band_type_num = gdal_type_number_locator(band_type)

        # Create information about the output file
        ds_out = driver.Create(out_file, cols, rows, 1, band_type_num)
        #Set the geotransform
        ds_out.SetGeoTransform(geotransform)
        #Set the projection
        ds_out.SetProjection(projection)
        #Get the band
        band_out = ds_out.GetRasterBand(1)
        # band_type_out = gdal.GetDataTypeName(band_out.DataType)

        # set the output array
        output_array = np.zeros([rows, cols])

        # read by block
        block_size_x = filter_column_size
        block_size_y = filter_row_size

        #Nested for loop that doesnt touch the edges
        #the edge values are set to zero

        #ensure the edges are to remain at zero (this should be changed later by duplicating the data for the edges
        y_edge_val = block_size_y - 1
        x_edge_val = block_size_x - 1

        for y in range(y_edge_val, rows-y_edge_val):
            for x in range(x_edge_val, cols-x_edge_val):
                data_sub = band.ReadAsArray(x, y, block_size_x, block_size_y)
                # multiply the kernel by the custom filter, and the sum becomes the middle number
                #The data_sub has some none values so this is how I am dealing with it
                if data_sub is None:
                    output_val = -9999
                else:
                    arr_mult = np.multiply(square_array, data_sub)
                    output_val = np.sum(arr_mult)
                #write this middle value to the new raster
                output_array[y, x] = output_val

        #write the data to the array
        band_out.WriteArray(output_array, 0, 0)
        #set to none to save memory
        band_out = None
        band = None
        ds = None
        ds_out = None


#=======================================================================================================================
#                   Test the Function(s)
#=======================================================================================================================


if(__name__ == "__main__"):
    pass
    # ds = gdal.Open(file_path, gdalconst.GA_ReadOnly)
    # zero_array = np.zeros((3,5))
    # print(zero_array)
    # row_size, column_size = np.shape(zero_array)
    # print('column size: {}, row size: {}'.format(column_size, row_size))
    # hahaha = 'qwerty.tif'
    # print(hahaha[-4:])
    # input_file = 'C:/Users/Chandler/Downloads/convolution_filters/s01Ls8_20160724.tif'
    input_file = 'F:/convolution_filters/s01Ls8_20160724.tif'
    band_nbr = 25 #NBR
    band_nir = 5 #nir
    # output_file = 'C:/Users/Chandler/Downloads/convolution_filters/s1_laplacian_4.tif'
    output_file = 'F:/convolution_filters/s1_laplacian_4_multi.tif'
    convolution = np.array([[0, -1, 0],
                            [-1, 4, -1],
                            [0, -1, 0]])
    # custom_filter(input_file, output_file, convolution, band_index=band_nbr)
    custom_filter(input_file, output_file, convolution)



