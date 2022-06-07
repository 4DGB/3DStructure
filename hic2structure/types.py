#
# Type Declarations
#

import typing as T
from collections.abc import Mapping, Set

import numpy as np
import numpy.typing as npt

########################
# DATA TYPES
########################

#
# Represents a series of contact records.
# This is a 3-column numpy array with columns for
# x-coordinate, y-coordinate and value
# (Indexed by record, then by column)
#
ContactRecords = T.NewType('ContactRecords', npt.NDArray[np.float64])

#
# Represents a set of contact records *without* any
# values. This is used to handle a "binary" contact
# map where each pair of coordinates either contacts or
# doesn't.
#
ContactSet = T.NewType('ContactSet', npt.NDArray[np.int64])

#
# Represents data for a single timestep of LAMMPS results
# This is a 7-column numpy array with the columns from the
# LAMMPS dump file. i.e: id, x, y, z, ix, iy, iz
# (Indexed by record, then by column)
#
LAMMPSTimestep = T.NewType('LAMMPSTimestep', npt.NDArray[np.float64])

#
# Represents a series of LAMMPSTimesteps, mapping integer
# timesteps to LAMMPSTimestep values
#
LAMMPSTimeseries = Mapping[int, LAMMPSTimestep]

########################
# SETTINGS TYPES
########################

class ContactRecordSettings(T.TypedDict):
    '''
    Represents settings for extracting contact records from
    a Hi-C file
    '''
    chromosome: str
    count_threshold: float
    distance_threshold: float
    resolution: int

class LAMMPSSettings(T.TypedDict):
    '''
    Represents settings for running LAMMPS on a series
    of contact records
    '''
    bond_coeff: int
    timesteps: int

class Settings(ContactRecordSettings, LAMMPSSettings):
    '''
    Represents settings for both extracting contact
    records and for running LAMMPS.
    i.e. the union of the fields in ContactRecordSettings
    and LAMMPSSettings
    '''
