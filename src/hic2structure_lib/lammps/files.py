"""
Module for dealing with LAMMPS data files
"""

import textwrap
from pathlib import Path

import numpy as np

from .util import random_walk, create_molecule_tags, create_bonds, create_angles

def write_inputfile(path, datafile_name, n, timesteps, bond_coeff, bondconnect):
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

            #restart 1000000 N{n}.restart

            read_data {datafile_name}
            reset_timestep 0

            write_data equilibrated_N{n}.dat

            group all type 1

            dump   1   all   custom   1000   sim.dump  id  x y z  ix iy iz
            dump_modify   1   format line "%d %.5f %.5f %.5f %d %d %d"

            angle_style   cosine
            angle_coeff   1 0.0

            pair_style      lj/cut 1.12246152962189
            pair_modify     shift yes
            pair_coeff      * * 1.0 1.0

            bond_style hybrid harmonic fene
            bond_coeff 1 fene 30.0 {bond_coeff} 1.0 1.0
            bond_coeff 2 harmonic  1.0 2.2
            special_bonds fene

            fix 1 all nve
            fix 2 all langevin   1.0 1.0   1.0   {lang}

            thermo 50000
            
            '''
        ))

        for i in range(len(bondconnect)):
            f.write(
                f'create_bonds single/bond 2 {int(bondconnect[i][0])} {int(bondconnect[i][1])} special yes\n'
            )

        f.write(textwrap.dedent(f'''\
            thermo_style   custom   step  temp  etotal epair  emol  press pxx pyy pzz lx ly lz pe ke ebond evdwl

            timestep 0.00001
            run {timesteps}'''
        ))

def write_datafile(path, n, lengths, spacing, dimensions):
    """
    Write a LAMMPS data file to the given path
    """
    chains = int(len(lengths))  # number of chains
    bond_number = int(sum(lengths) - chains) # number of bonds

    angle_number = 0
    for length in lengths: 
        if length > 2.0:
            angle_number += int(length - 2)  # number of bond angles

    lattice_coords = random_walk(n) * spacing  # coordinates of lattice points
    tags = create_molecule_tags(n, lengths)  # molecule tags
    bonds = create_bonds(n, lengths)  # indicates bonds between particles
    angles = create_angles(n, lengths)  # indicates angles between particles

    with open(path, 'w') as f:
        f.write(textwrap.dedent(f'''\
            LAMMPS data file for random 3D walk on lattice: N = {n}, Chain length = {length}

            {n} atoms
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

        for i in range(n):
            f.write(f'\n{i + 1}\t{tags[i]}\t1\t{lattice_coords[i][0]}\t{lattice_coords[i][1]}\t{lattice_coords[i][2]}\t0\t0\t0')
        if bond_number > 0:
            f.write('\n\nBonds\n')
            for i in range(len(bonds)):
                f.write(f'\n{i + 1}\t1\t{bonds[i][0]}\t{bonds[i][1]}')
        if angle_number > 0:
            f.write('\n\nAngles\n')
            for i in range(len(angles)):
                f.write(f'\n{i + 1}\t1\t{angles[i][0]}\t{angles[i][1]}\t{angles[i][2]}')

def write_input_deck(dir: Path, timesteps, bond_coeff, records):
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
    inputfile = dir.joinpath('in.input')
    datafile  = dir.joinpath(datafile_name)

    # Create files
    write_datafile(datafile, n, lengths, spacing, dimensions)
    write_inputfile(inputfile, datafile_name, n, timesteps, bond_coeff, records)

def read_dumpfile(path: Path):
    """
    Read in a LAMMPS output dump
    """
    f = open(path, 'r')
    lines = list(map(
        str.strip,
        f.read().splitlines()
    ))
    f.close()

    dump = {}
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
        
        dump[timestep] = data
        i = end_line

    return dump

