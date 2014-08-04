# Module for the BNL image processing project
# Developed at the NSLS-II, Brookhaven National Laboratory
# Developed by Gabriel Iltis, Nov. 2013
"""
This function reads an AmiraMesh binary file and returns a set of two objects.
First, a numpy array containing the image data set, and second, a metadata dictionary
containing all header information both pertaining to the image data set, and required
to write the image data set back in AmiraMesh file format.
"""

import numpy as np
import os

def _read_amira (src_file):
    """
    This function reads all information contained within standard AmiraMesh
    data sets, and separates the header information from actual image, or 
    volume, data. The function then outputs two lists of strings. The first, 
    am_header, contains all of the raw header information. The second, am_data,
    contains the raw image data.
    NOTE: Both function outputs will require additional processing in order to
    be usable in python and/or with the NSLS-2 function library.
    
    Parameters
    ----------
    src_file : string
        The path and file name pointing to the AmiraMesh file to be loaded.
    
    
    Returns
    -------
    am_header : List of strings
        This list contains all of the raw information contained in the AmiraMesh
        file header. Each line of the original header has been read and stored
        directly from the source file, and will need some additional processing
        in order to be useful in the analysis of the data using the NSLS-2 
        image processing function set.
    
    am_data : string
        A compiled string containing all of the image array data, that was stored
        in the source AmiraMesh data file.  
    """
    
    am_header = []
    am_data = []
    f = open(os.path.normpath(src_file), 'r')
    while True:
        line = f.readline()
        am_header.append(line)
        if (line == '# Data section follows\n'):
            f.readline()
            break
    am_data = f.read()
    f.close()
    return am_header, am_data


def _cnvrt_amira_data_2numpy (am_data, header_dict, flip_Z = True):
    """
    This function takes the data object generated by "_read_amira", which 
    contains all of the image array data formated as a string and converts the 
    string into a numpy array of the dtype stipulated in the AmiraMesh header 
    dictionary.  The standard format for Avizo Binary files is IEEE binary. 
    Big or little endian-ness is stipulated in the header information, and is 
    be assessed and taken into account by this function as well, during the 
    conversion process.
    
    Parameters
    ----------
    am_data : string
        String object containing all of the image array data, formatted as IEEE 
        binary. Current dType options include:
            float
            short
            ushort
            byte
    
    header_dict : md_dict
        Metadata dictionary containing all relevant attributes pertaining to the
        image array. This metadata dictionary is the output from the function 
        "_create_md_dict."
    
    flip_Z : bool
        This option is included because the .am data sets evaluated thus far
        have opposite z-axis indexing than numpy arrays. This switch currently
        defaults to "True" in order to ensure that z-axis indexing remains
        consistent with data processed using Avizo.
        Setting this switch to "True" will flip the z-axis during processing,
        and a value of "False" will keep the array is initially assigned during 
        the array reshaping step.
    
    Returns
    -------
    output : ndarray
        Numpy ndarray containing the image data converted from the AmiraMesh
        file. This data array is ready for further processing using the NSLS-II
        function library, or other operations able to operate on numpy arrays.
    """
    Zdim = header_dict['array_dimensions']['z_dimension']
    Ydim = header_dict['array_dimensions']['y_dimension']
    Xdim = header_dict['array_dimensions']['x_dimension']
    #Strip out null characters from the string of binary values
    data_strip = am_data.strip('\n')
    #Dictionary of the encoding types for AmiraMesh files
    am_format_dict = {'BINARY-LITTLE-ENDIAN' : '<',
                      'BINARY' : '>',
                      'ASCII' : 'unknown'
                     }
    #Dictionary of the data types encountered so far in AmiraMesh files
    am_dtype_dict = {'float' : 'f4',
                     'short' : 'h4',
                     'ushort' : 'H4',
                     'byte' : 'b'
                         }
    if header_dict['data_format'] == 'BINARY-LITTLE-ENDIAN':
        flt_values = np.fromstring(data_strip, 
                                   (am_format_dict[header_dict['data_format']] + 
                                       am_dtype_dict[header_dict['data_type']]))
    #Resize the 1D array to the correct ndarray dimensions
    flt_values.resize(Zdim, Ydim, Xdim)
    if flip_Z == True:
        output = flt_values[::-1, ..., ...]
    else:
        output = flt_values
    return output

def _sort_amira_header (header_list):
    """
    This function takes the raw string list containing the AmiraMesh header
    informationa and strips the string list of all "empty" characters,
    including new line characters ('\n') and empty lines. The function also
    splits each header line (which originally is stored as a single string)
    into individual words, numbers or characters, using spaces between words as
    the separating operator. The output of this function is used to generate
    the metadata dictionary for the image data set.

    Parameters
    ----------
    header_list : list of strings
        This is the header output from the function _read_amira()
    
    Returns
    -------
    header_list : list of strings
        This header list has been stripped and sorted and is now ready for
        populating the metadata dictionary for the image data set.
    """
    
    for row in range(len(header_list)):
        header_list[row] = header_list[row].strip('\n')
        header_list[row] = header_list[row].split(" ")
        for column in range(len(header_list[row])):
            header_list[row] = filter(None, header_list[row])
    header_list = filter(None, header_list)
    return header_list

def _create_md_dict (header_list):
    """
    This function takes the sorted header list as input and populates the
    metadata dictionary containing all relevant header information pertinent to
    the image data set originally stored in the AmiraMesh file.

    Parameters
    ----------
    header_list : list of strings
        This is the output from the _sort_amira_header function.
    
    """

    md_dict = {'software_src' : header_list[0][1], #Avizo specific
               'data_format' : header_list[0][2], #Avizo specific
               'data_format_version' : header_list[0][3] #Avizo specific
                }
    for row in range(len(header_list)):
        try:
            md_dict['array_dimensions'] = {'x_dimension' : int(header_list[row]
                                                   [header_list[row]
                                                       .index('define') + 2]),
                                     'y_dimension' : int(header_list[row]
                                                   [header_list[row]
                                                       .index('define') + 3]),
                                     'z_dimension' : int(header_list[row]
                                                   [header_list[row]
                                                       .index('define') + 4])
                                     }
        except:
        #    continue
            try:
                md_dict['data_type'] = header_list[row][header_list[row]
                        .index('Content') + 2]
            except: 
            #    continue
                try:
                    md_dict['coord_type'] = header_list[row][header_list[row]
                            .index('CoordType') + 1]
                except:
                    try:
                        #TODO: add "voxel_size" computation, 
                        #       and Check for anisotropy
                        md_dict['bounding_box'] = {'x_min' : 
                                                    float(
                                                        header_list[row][
                                                            header_list[row]
                                                            .index(
                                                                'BoundingBox')
                                                            + 1]),
                                                   'x_max' : 
                                                   float(header_list[row][
                                                        header_list[row]
                                                        .index('BoundingBox')
                                                        + 2]),
                                                   'y_min' : 
                                                   float(header_list[row][
                                                        header_list[row]
                                                        .index('BoundingBox')
                                                        + 3]),
                                                   'y_max' : 
                                                   float(header_list[row][
                                                        header_list[row]
                                                        .index('BoundingBox')
                                                        + 4]),
                                                   'z_min' : 
                                                   float(header_list[row][
                                                        header_list[row]
                                                        .index('BoundingBox')
                                                        + 5]),
                                                   'z_max' : 
                                                   float(header_list[row][
                                                        header_list[row]
                                                        .index('BoundingBox')
                                                        + 6])
                                                   }
                    except:
                        try:
                            md_dict['units'] = (header_list[row][
                                header_list[row].index('Units') + 2])
                            md_dict['coordinates'] = header_list[row + 1][1]
                        except:
                            continue
    return md_dict

def load_am_as_np(file_path):
    """
    This function will load and convert an AmiraMesh binary file to a numpy 
    array. All pertinent information contained in the .am header file is written
    to a metadata dictionary, which is returned along with the numpy array 
    containing the image data.
    
    Parameters
    ----------
    file_path : string
        The path and file name of the AmiraMesh file to be loaded.
    
    Returns
    -------
    md_dict : dictionary
        Dictionary containing all pertinent header information associated with 
        the data set.
    
    np_array : float ndarray
        An ndarray containing the image data set to be loaded. Values contained 
        in the resulting volume are set to be of float data type by default.
    """
    
    header, data = _read_amira(file_path)
    header = _sort_amira_header(header)
    md_dict = _create_md_dict(header)
    np_array = _cnvrt_amira_data_2numpy(data, md_dict)
    return md_dict, np_array
