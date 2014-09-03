#!/usr/bin/env python

import bob.db.lfw
import facereclib

lfw_directory = "[YOUR_LFW_DIRECTORY]"

database = facereclib.databases.DatabaseXBob(
    database = bob.db.lfw.Database(
        original_directory = lfw_directory,
        annotation_type = 'funneled'
    ),
    name = 'lfw',
    original_directory = lfw_directory,
    original_extension = ".jpg",
    protocol = 'view1',

    all_files_options = {'world_type' : 'unrestricted'},
    extractor_training_options = {'world_type' : 'unrestricted'}, # 'subworld' : 'twofolds'
    projector_training_options = {'world_type' : 'unrestricted'}, # 'subworld' : 'twofolds'
    enroller_training_options =  {'world_type' : 'unrestricted'} # 'subworld' : 'twofolds'
)
