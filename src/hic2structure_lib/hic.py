from io import BufferedReader
from pathlib import Path
import struct

import numpy as np
from straw import straw

"""
Module for dealing with Hi-C data files
"""

def _readcstr(f):
    """
    Helper function for reading in C-style string from file
    """
    buf = b""
    while True:
        b = f.read(1)
        if b is None or b == b"\0":
            return buf.decode("utf-8")
        elif b == "":
            raise EOFError("Buffer unexpectedly empty while trying to read null-terminated string")
        else:
            buf += b

class HICError(Exception):
    pass

class HICMetadata:
    """
    Represents the Metadata of a Hi-C File
    """

    def __init__(self, f: BufferedReader):
        """
        Load metadata from the given filehandle.

        This particular function is copied from the read_metadata function of
        the (older version of) the hic-straw module from Aiden Labs, with some
        modifications for readability/usability.

        Note that we still use the *actual* hic-straw module as well
        (installed through pip, like our other dependencies), but the current
        version of that is missing the read_metadata function, hence its
        reimplementation here.

        Authors: Yue Wu, Neva Durand, Yossi Eliaz, Muhammad Shamim, Erez Aiden
        License: MIT
        """

        # Verify magic string
        magic_string = struct.unpack('<3s', f.read(3))[0]
        f.read(1)
        if (magic_string != b'HIC'):
            raise HICError(f"Incorrect magic string. Expected 'HIC', Got '{magic_string}'")

        # Read other metadata
        self.version = struct.unpack('<i',f.read(4))[0]
        self.master_index = struct.unpack('<q',f.read(8))[0]

        # Read Genome
        genome = ""
        c=f.read(1).decode("utf-8") 
        while (c != '\0'):
            genome += c
            c=f.read(1).decode("utf-8") 
        self.genome_id=genome

        # Read NVI
        if (self.version > 8):
            nvi = struct.unpack('<q',f.read(8))[0]
            nvisize = struct.unpack('<q',f.read(8))[0]
            self.nvi = nvi
            self.nvi_size = nvisize
        else:
            self.nvi = None
            self.nvi_size = None

        # Read attribute dictionary (stats+graphs)
        nattributes = struct.unpack('<i',f.read(4))[0]
        self.attributes = {}
        for _ in range(0, nattributes):
            key = _readcstr(f)
            value = _readcstr(f)
            self.attributes[key]=value

        # Read Chromosomes
        nChrs = struct.unpack('<i',f.read(4))[0]
        self.chromosomes = {}
        for _ in range(0, nChrs):
            key = _readcstr(f)
            if (self.version > 8):
                value = struct.unpack('q',f.read(8))[0]
            else:
                value = struct.unpack('<i',f.read(4))[0]
            self.chromosomes[key]=value

        # Read base-pair resolutions
        nBpRes = struct.unpack('<i',f.read(4))[0]
        self.basepair_resolutions = []
        for _ in range(0, nBpRes):
            res = struct.unpack('<i',f.read(4))[0]
            self.basepair_resolutions.append(res)

        # Read fragment resolutions
        nFrag = struct.unpack('<i',f.read(4))[0]
        self.fragment_resolutions = []
        for _ in range(0, nFrag):
            res = struct.unpack('<i',f.read(4))[0]
            self.fragment_resolutions.append(res)

class HIC:
    """
    Represents a Hi-C File
    """

    def __init__(self, filename):
        """
        Load the given Hi-C file.
        Only the metadata will be loaded initially. You can
        load contact records with the getContactRecords method
        """
        path = Path(filename).resolve()
        if not path.exists():
            raise IOError(f"File, '{filename}' does not exist.")

        self.path = path

        with open(filename, 'rb') as f:
            self.metadata = HICMetadata(f)

    def get_contact_records(self, chromosome, resolution, threshold):
        # Load records via hic-straw

        # Check that chromosome and resolution are valid
        if chromosome not in self.metadata.chromosomes:
            allowed = list( self.metadata.chromosomes.keys() )
            raise HICError(
                f"Chromosome '{chromosome}' is not available. "
                f"Available chromomesomes are: {allowed}"
            )

        if resolution not in self.metadata.basepair_resolutions:
            allowed = self.metadata.basepair_resolutions
            raise HICError(
                f"Resolution '{resolution}' is not available. "
                f"Available resolutions are: {allowed}"
            )

        # hic-straw exits ungracefully on error,
        # (because of course it does), so we try to
        # catch it with a try/except
        try:
            # Run hic-straw
            records = straw(
                'observed',
                'KR',
                str(self.path),
                chromosome,
                chromosome,
                'BP',
                resolution
            )
            if not records:
                raise ValueError("No contact records found.")
        except SystemExit as e:
            raise RuntimeError("Failed to load contact records")

        # Convert to numpy table
        # each row indexed by [binX, binY, counts]
        table = np.zeros((len(records), 3))
        index = 0 
        for contact in records:
            table[index][0] = int(contact.binX)
            table[index][1] = int(contact.binY)
            table[index][2] = contact.counts
            index += 1

        # Convert coordinates to units of resolution. i.e. particle numbers
        table[:, 0] //= resolution
        table[:, 1] //= resolution
        table[:, 0] += 1
        table[:, 1] += 1

        # Filter by threshold
        table = table[ table[:,2] > threshold ]
        # Filter out self-contacts
        table = table[ table[:,0] != table[:,1] ]

        return table
