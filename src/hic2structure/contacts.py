"""
Module for dealing with Contact Maps
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform

from .types import LAMMPSTimestep, ContactRecordSettings, ContactRecords

def find_contacts(data: LAMMPSTimestep, settings: ContactRecordSettings) -> ContactRecords:
    """
    Get contacts from a LAMMPS output dump
    """
    coords = data[:,1:4]
    IDs = data[:,0]

    distances = np.triu( squareform(pdist(coords)) )
    contact_IDarrays = np.where(
        ( distances < settings['distance_threshold'] ) & ( distances > 0 )\
    )

    C = np.ma.size( contact_IDarrays[0] )
    contact_IDs = np.hstack(
        (
            np.reshape( np.take(IDs,contact_IDarrays[0]), (C,1) ),
            np.reshape( np.take(IDs,contact_IDarrays[1]), (C,1) )
        )
    )

    contacts = np.hstack(
        (
            np.reshape( contact_IDs[:,0], (C,1) ),
            np.reshape( contact_IDs[:,1], (C,1) ),
            distances[
                np.reshape( contact_IDarrays[0], (C,1) ),
                np.reshape( contact_IDarrays[1], (C,1) )
            ]
        )
    ) 

    return ContactRecords(contacts)
