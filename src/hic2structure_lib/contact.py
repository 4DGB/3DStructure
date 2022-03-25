"""
Module for dealing with Contact Maps
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform

def find_contacts(data, dist=3.3):
    """
    Get contacts from a LAMMPS output dump
    """
    last_timestep = sorted( data.keys() )[-1]
    coords = data[last_timestep][:,1:4]
    IDs = data[last_timestep][:,0]

    distances = np.triu(squareform(pdist(coords)))
    contact_IDarrays = np.where((distances<dist) & (distances>0))

    C = np.ma.size(contact_IDarrays[0])
    contact_IDs = np.hstack((np.reshape(np.take(IDs,contact_IDarrays[0]), (C,1)), np.reshape(np.take(IDs,contact_IDarrays[1]), (C,1))))   
    contacts = np.hstack((np.reshape(contact_IDs[:,0], (C,1)), np.reshape(contact_IDs[:,1], (C,1)), distances[np.reshape(contact_IDarrays[0], (C,1)), np.reshape(contact_IDarrays[1], (C,1))])) 

    return contacts

