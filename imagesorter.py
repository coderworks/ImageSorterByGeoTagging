
""" ============================================================
imageSorterByGeoTagging.py

This script can be run from a root directory of images and searches for These
images in folders and in subfolders. These images are then scanned for 'GPSInfo'
in the metadata and sorted in folders based on a precision number that
determines different locations.

Tweak the "precision" parameter to improve filtering of locations

~FT 11-2020~
 ============================================================ """

import os

from glob import glob
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS

""" ========================================================= """

# Global
debug = False

# Decimal places | Decimal degrees | DMS              | Comment
# 0              | 1.0             | 1° 00′ 0″        | country or large region
# 1              | .1              | 0° 06′ 0″        | large city or district
# 2              | .01             | 0° 00′ 36″       | town or village
# 3              | .001            | 0° 00′ 3.6″      | neighborhood, street
# 4              | .0001           | 0° 00′ 0.36″     | individual street, land parcel
# 5              | .00001          | 0° 00′ 0.036″    | individual trees, door entrance
# 6              | .000001         | 0° 00′ 0.0036″   | individual humans
# 7              | .0000001        | 0° 00′ 0.00036″  | practical limit of commercial surveying
# 8              | .00000001       | 0° 00′ 0.000036″ | specialized surveying (e.g. tectonic plate mapping)
# * source for precision wikipedia
precision = 5 # decimal places

""" ========================================================= """

# Functions
def getExif(filename):

    image = Image.open(filename)
    image.verify()

    return image.getexif()

def getGeoTaggs(exif):

    geoTaggs = {}

    if exif:
        for (idx, tag) in TAGS.items():
            if tag == 'GPSInfo':
                if idx not in exif:
                    if debug:
                        print("No EXIF geotaggs found.")
                    break

                for (key, val) in GPSTAGS.items():
                    if key in exif[idx]:
                        geoTaggs[val] = exif[idx][key]

    else:
        if debug:
            print("No EXIF metadata found.")

    return geoTaggs

def findMissing(lst):
    return [x for x in range(lst[0], lst[-1]+1) if x not in lst]

def tupleToList(value):

    string = str(value)

    if "." in string:
        list = string.split(".")
    # somethimes "," is used
    else:
        string = string[1:-1] # remove '(' and ')', this seems to be differnt from "."
        list = string.split(",")

    return list

def checkIfZero(value):

    i = int(value)

    return i if i > 0 else 1

def getDecimalFromDms(dms, reference):

    # convert tuple with tuples to list elements
    d, m, s = dms
    deg = tupleToList(d)
    min = tupleToList(m)
    sec = tupleToList(s)

    # calculate and prevent the by zero division
    degrees = checkIfZero(deg[0]) / checkIfZero(deg[1])
    minutes = checkIfZero(min[0]) / checkIfZero(min[1]) / 60.0
    seconds = checkIfZero(sec[0]) / checkIfZero(sec[1]) / 3600.0

    # change orientation if needed
    if reference in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    # return decimal
    return round(degrees + minutes + seconds, 10)

def getCoordinates(geoTags):

    lat = getDecimalFromDms(geoTags['GPSLatitude'], geoTags['GPSLatitudeRef'])
    lon = getDecimalFromDms(geoTags['GPSLongitude'], geoTags['GPSLongitudeRef'])

    return (lat,lon)

def checkWithinBoundries(value, reference):

    # split lists
    a, b = value
    c, d = reference

    # round values and merge back
    value = [round(a, precision), round(b, precision)]
    reference = [round(c, precision), round(d, precision)]

    if debug:
        print("Checkbounds a: ", value)
        print("Checkbounds b: ", reference)

    if value == reference: # compare
        return True # if within boundries
    return False # else outside boundries

def createDirectory(foldername):
    try:
        os.mkdir(foldername)
    except OSError:
        if debug:
            print ("Creation of the directory %s failed." % foldername)
    else:
        if debug:
            print ("Successfully created the directory %s." % foldername)

""" ========================================================= """

# Main

# setup list for survey locations
locations = []

# get current working dir
path = os.getcwd()
print("Current working directory: ", path)

# harvest and filter files found
files = glob('*.jpg') + glob('*.JPG') + glob('*.jpeg') + glob('*.JPEG')
for file in files:

    geoTaggs = getGeoTaggs(getExif(file))

    if debug:
        print("<---------------->")
        print(file)
        print(geotagging)

    if geoTaggs:
        imageCoordinates = getCoordinates(geoTaggs)

        # setup this stage
        newLocation = True
        locationsIndex = len(locations) # new location

        # run until found, else do nothing
        for location in locations:

            # checkWithinBoundries checks with a precision limmiter
            # to broaden the search
            if checkWithinBoundries(imageCoordinates, location):
                newLocation = False
                locationsIndex = locations.index(location) # existing location
                break

        # copy file to destination
        directory = "Location" + str(locationsIndex)
        if debug:
            print("Directory " + directory)

        if newLocation:
            locations.append(imageCoordinates)
            createDirectory(directory)

            if debug:
                print("New location detected.")

        else:
            if debug:
                print("Location already available.")

        # copy the file
        os.popen("cp " + file + " " + directory + "/" + file)

        if debug:
            print("cp " + file + " " + directory + "/" + file)


""" ========================================================= """
