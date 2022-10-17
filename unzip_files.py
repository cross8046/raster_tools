#modified from here: https://stackoverflow.com/questions/31346790/unzip-all-zipped-files-in-a-folder-to-that-same-folder-using-python-2-7-5

import os, zipfile



def unzip_files(dir_name, extension):
    '''
    Unzips folders in a folder
    :param dir_name: name of the directory; string
    :param extension: file extension of folders I wish to unzip; string
    :return: unzipped folders
    '''

    os.chdir(dir_name)  # change directory from working dir to dir with files

    for item in os.listdir(dir_name):  # loop through items in dir
        if item.endswith(extension):  # check for ".zip" extension
            file_name = os.path.abspath(item)  # get full path of files
            zip_ref = zipfile.ZipFile(file_name)  # create zipfile object
            zip_ref.extractall(dir_name)  # extract file to dir
            zip_ref.close()  # close file
            os.remove(file_name)  # delete zipped file

# =======================================================================================================================
#                   Run the script
# =======================================================================================================================

if __name__ == '__main__':
    dir_name = 'C:/Users/Chand/Downloads/DATA/mtbs/2020/'
    extension = ".zip"

    unzip_files(dir_name, extension)