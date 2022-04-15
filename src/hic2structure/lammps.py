'''
Module for interacting with LAMMPS.

That is, running it and reading/writing its input
and ouput files.
'''

import os
import shutil
import time
from pathlib import Path
import subprocess as sub
import tempfile as temp
from contextlib import contextmanager

import textwrap
import numpy as np
import numpy.typing as npt

from .types import LAMMPSSettings, ContactRecords, LAMMPSTimeseries, LAMMPSTimestep

########################
# HELPER FUNCTIONS
########################

# function to check if next site is already occupied
def check_if_free(lattice_coords, next_coords, index):
    for i in range(index):
        if lattice_coords[i][0] == next_coords[0] and lattice_coords[i][1] == next_coords[1] \
                and lattice_coords[i][2] == next_coords[2]:
            return False
    return True

# function to create random 3D walk on lattice
def random_walk(n):
    backtrack = 10
    lattice_coords = np.zeros([n, 3])
    steps = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
                      [-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, -1.0]])
    i = 1
    while i < n:
        issue = False
        s = time.time()
        #if i % 100 == 0:
            #print(i, s-start, 's')
        rand = np.random.randint(0, 6)
        next_coords = lattice_coords[i - 1] + steps[rand]
        while check_if_free(lattice_coords, next_coords, i) == False:
            rand = np.random.randint(0, 6)
            next_coords = lattice_coords[i-1] + steps[rand]
            e = time.time()
            if e - s > 0.1:
                issue = True
                #print('Stuck! Go back and find a new way... %s' % i)
                for k in range(1, backtrack + 1):
                    lattice_coords[i-k] = np.zeros(3)
                i -= backtrack + 1
                break
        if issue == False:
            lattice_coords[i] = next_coords
            i += 1
    return lattice_coords

# function to create molecule tags
def create_molecule_tags(n, lengths):
    tags = []
    tag = 1
    cumlength = np.cumsum(lengths)
    for i in range(1, n+1):
        if i - 1 in cumlength:
            tag += 1
        tags.append(tag)

    return tags

# function to create bonds
def create_bonds(n, lengths):
    bonds = []
    cumlength = np.cumsum(lengths)
    for i in range(1, n):
        if i not in cumlength:
            bonds.append([i, i+1])
    return bonds


# function to create angles
def create_angles(n, lengths):
    angles = []
    cumlength = np.cumsum(lengths)
    for i in range(1, n-1):
        if (i not in cumlength) and (i+1 not in cumlength):
            angles.append([i, i + 1, i + 2])
    return angles

########################
# FILE I/O
########################

def write_inputfile(
    path: Path, datafile_name: str,
    num_segments: int, settings: LAMMPSSettings,
    records: ContactRecords    
):
    """
    Write a LAMMPS input file to the given path
    """
    with open(path, 'w') as f:
        lang = np.random.randint(1,1000000) # random noise term for langevin

        f.write(textwrap.dedent(f'''\
            log sim.log
            units lj

            atom_style angle
            boundary        p p p

            neighbor 4 bin
            neigh_modify every 1 delay 1 check yes

            atom_modify sort 0 0

            #restart 1000000 N{num_segments}.restart

            read_data {datafile_name}
            reset_timestep 0

            write_data equilibrated_N{num_segments}.dat

            group all type 1

            dump   1   all   custom   1000   sim.dump  id  x y z  ix iy iz
            dump_modify   1   format line "%d %.5f %.5f %.5f %d %d %d"

            angle_style   cosine
            angle_coeff   1 0.0

            pair_style      lj/cut 1.12246152962189
            pair_modify     shift yes
            pair_coeff      * * 1.0 1.0

            bond_style hybrid harmonic fene
            bond_coeff 1 fene 30.0 {settings['bond_coeff']} 1.0 1.0
            bond_coeff 2 harmonic  1.0 2.2
            special_bonds fene

            fix 1 all nve
            fix 2 all langevin   1.0 1.0   1.0   {lang}

            thermo 50000
            
            '''
        ))

        for r in records:
            f.write(
                f'create_bonds single/bond 2 {int(r[0])} {int(r[1])} special yes\n'
            )

        f.write(textwrap.dedent(f'''\
            thermo_style   custom   step  temp  etotal epair  emol  press pxx pyy pzz lx ly lz pe ke ebond evdwl

            timestep 0.00001
            run {settings['timesteps']}'''
        ))

def write_datafile(
    path: Path, num_segments: int,
    lengths: list[int], spacing: float,
    dimensions
):
    """
    Write a LAMMPS data file to the given path
    """
    chains = int(len(lengths))  # number of chains
    bond_number = int(sum(lengths) - chains) # number of bonds

    angle_number = 0
    length = 0
    for l in lengths: 
        if l > 2.0:
            angle_number += int(l - 2)  # number of bond angles
        length = l

    lattice_coords = random_walk(num_segments) * spacing  # coordinates of lattice points
    tags = create_molecule_tags(num_segments, lengths)  # molecule tags
    bonds = create_bonds(num_segments, lengths)  # indicates bonds between particles
    angles = create_angles(num_segments, lengths)  # indicates angles between particles

    with open(path, 'w') as f:
        f.write(textwrap.dedent(f'''\
            LAMMPS data file for random 3D walk on lattice: N = {num_segments}, Chain length = {length}

            {num_segments} atoms
            1 atom types
            {bond_number} bonds
            2 bond types
            1000 extra bond per atom
            {angle_number} angles
            1 angle types

            {-dimensions[0]/2} {dimensions[0]/2} xlo xhi
            {-dimensions[1]/2} {dimensions[1]/2} ylo yhi
            {-dimensions[2]/2} {dimensions[2]/2} zlo zhi

            Masses

            1 1

            Atoms
            '''
        ))

        for i in range(num_segments):
            f.write(f'\n{i + 1}\t{tags[i]}\t1\t{lattice_coords[i][0]}\t{lattice_coords[i][1]}\t{lattice_coords[i][2]}\t0\t0\t0')
        if bond_number > 0:
            f.write('\n\nBonds\n')
            for i in range(len(bonds)):
                f.write(f'\n{i + 1}\t1\t{bonds[i][0]}\t{bonds[i][1]}')
        if angle_number > 0:
            f.write('\n\nAngles\n')
            for i in range(len(angles)):
                f.write(f'\n{i + 1}\t1\t{angles[i][0]}\t{angles[i][1]}\t{angles[i][2]}')

def write_input_deck(dir: Path, settings: LAMMPSSettings, records: ContactRecords):
    """
    Write a LAMMPS input file and data file into the given
    directory for a simulation on the given contact records
    """

    # Defining LAMMPS properties
    n = int(max(records.max(axis = 0)[0], records.max(axis = 0)[1]))  # total number of particles
    lengths = [n]  # length of chains
    spacing = 3.0  # lattice spacing
    lattice_numbers = np.array([200, 200, 200])
    dimensions = lattice_numbers * 2  # dimensions of box

    datafile_name=f"random_coil_N{n}.dat"

    dir.mkdir(parents=True, exist_ok=True)
    inputfile = dir / 'in.input'
    datafile  = dir / datafile_name

    # Create files
    write_datafile(datafile, n, lengths, spacing, dimensions)
    write_inputfile(inputfile, datafile_name, n, settings, records)

def read_dumpfile(path: Path) -> LAMMPSTimeseries:
    """
    Read in a LAMMPS output dump
    """
    f = open(path, 'r')
    lines = list(map(
        str.strip,
        f.read().splitlines()
    ))
    f.close()

    dump: LAMMPSTimeseries = {}
    i = 0
    # finds coordinates using "ITEM:" directives
    # creates a dict with timestep and coordinates
    while i < len(lines):
        timestep_line = lines.index("ITEM: TIMESTEP", i) + 1
        timestep = int(lines[timestep_line])

        # Get the slice of coordinate lines between the start
        # of this timestep and the next
        begin_line = lines.index("ITEM: ATOMS id x y z ix iy iz", i)
        try:
            end_line = lines.index("ITEM: TIMESTEP", i+1)
        except ValueError:
            end_line = len(lines)
        coords = lines[begin_line+1:end_line]

        # Parse coordinates
        data = np.zeros( (len(coords), 7 ))
        for (j, line) in enumerate(coords):
            vals = line.split()
            data[j][0] = int(   vals[0] )
            data[j][1] = float( vals[1] )
            data[j][2] = float( vals[2] )
            data[j][3] = float( vals[3] )
            data[j][4] = float( vals[4] )
            data[j][5] = float( vals[5] )
            data[j][6] = float( vals[6] )
        
        dump[timestep] = LAMMPSTimestep(data)
        i = end_line

    return dump

########################
# RUNNING LAMMPS
########################

class LAMMPSError(Exception):
    pass

# A context-manager to run a block of code
# in a different directory
# Thanks, StackOverflow! https://stackoverflow.com/a/24469659/2827258
@contextmanager
def cd_context(dir):
    original=os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(original)

def run_lammps(
    records: ContactRecords, settings: LAMMPSSettings,
    lammps_exec:str='lmp', copy_log_to:Path=None
) -> LAMMPSTimeseries:
    '''
    Run a LAMMPS simulation in a temporary directory. You can set the path to
    LAMMPS executable with 'lammps_exec' and optionally copy the log file
    to a given path with 'copy_log_to'
    '''

    copy_dest = copy_log_to.resolve() if copy_log_to else None

    with temp.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        write_input_deck(tmp, settings, records)

        with cd_context(tmpdir):
            proc = sub.run(
                [lammps_exec, '-in', 'in.input'],
                stdout=sub.DEVNULL # we'll copy the log if we want
                                   # to see output
            )
            try:
                proc.check_returncode()
            except sub.CalledProcessError as e:
                raise LAMMPSError(f"LAMMPS exited with error: {e}")

            data = read_dumpfile( Path('sim.dump') )

            if copy_dest is not None:
                shutil.copy2( 'sim.log', copy_dest )

    return data
