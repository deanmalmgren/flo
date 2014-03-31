
# https://github.com/alexis-mignon/python-flickr-api/wiki/Tutorial

import sys
import os

import flickr_api

out_directory = sys.argv[1]

# arbitrarily chose the top flickr photographer from here
# http://www.flickrooster.com/
username = "mathewroberts"

print dir(flickr_api)
print dir(flickr_api.Person)
user = flickr_api.Person.findByUsername(username)
photos = user.getPublicPhotos()
print dir(photos)
