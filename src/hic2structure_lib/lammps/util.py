"""
Helper functions
"""

import time

import numpy as np

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
