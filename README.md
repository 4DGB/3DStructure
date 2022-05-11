# 🧬 hic2structure 🧬

An adaptation of [this Google Colab Notebook](https://colab.research.google.com/drive/1V4CRdM_hOt4KcM7jBFWjQ6NQyWxECim3?usp=sharing#scrollTo=jftgNJG89Fk9) for processing Hi-C data files, running the LAMMPS Molecular Dynamics simulation and creating structure data. It has been rewritten to work as a command-line script and python module.

## Setup

1. Set up your Python virtual environment
```sh
virtualenv venv/
source venv/bin/activate
pip3 install -r requirements.txt
```

2. Install [LAMMPS](https://www.lammps.org/). You may be able to install it with your distro's package manager, or you can download and build it from source.

3. Install the module
```
cd src/
python3 setup.py install
```

## Run Script

```sh
python3 -m hic2structure --verbose HIC_FILE
```

This will load contact records from the given Hi-C file and run a LAMMPS simulation on in it in a temporary directory, creating an output structure data file and a copy of the LAMMPS log in the directory `./out`.

You can change many settings (which resolution to load from the Hi-C file, which chromosome, how many timesteps to run the simulation, etc.) with command-line arguments. For example:

```sh
python3 -m hic2structure --verbose --resolution 200000 --threshold 2.5 --chromosome 22 HIC_FILE
```

You can run `python3 -m hic2structure --help` to see all the available options and and their default values.

## Use as a module

If you need finer control over things, you can import `hic2structure` into a script. Most functions exported by the module and its submodules revolve around a "settings" dictionary with the same sort of parameters as above.

For example, the below script will get a contact map from a Hi-C file, output it, then run LAMMPS and output the new, simulated, contacts.

```python
#!/usr/bin/env python3

from gettext import find
from pathlib import Path

from hic2structure.types import Settings
from hic2structure.hic import HIC
from hic2structure.lammps import run_lammps
from hic2structure.out import write_contact_set, contact_records_to_set
from hic2structure.contacts import find_contacts

settings: Settings = {
    'resolution': 200000,
    'threshold': 2.5,
    'chromosome': '22',
    'bond_coeff': 50,
    'timesteps': 100000
}

hic = HIC( Path('my_input.hic') )

real_contacts = hic.get_contact_records(settings)

write_contacts(Path('real_contactmap.tsv'), real_contacts)

lammps_data = run_lammps( contact_records_to_set(real_contacts), settings)

# the run_lammps result is indexed by timestep
last_timestep = lammps_data[100000]

simulated_contacts = find_contacts(last_timestep, settings)

write_contact_set(Path('simulated_contactmap.tsv'), simulated_contacts)

```

## How Contact Records are used/represented

When contact records are read from the Hi-C file, all the records with a value below the threshold (set with the `--count-threshold` argument) are excluded and then the values for the remaining contacts are discarded. Effectively, this makes a "binary" contact map where each pair of coordinates either contacts or doesn't, with no values inbetween. In this case, only the coordinates with a count greater than the threshold are included.

These records are used as input to the LAMMPS simulation which then comes up with a 3D structure. The coordinates in 3D space for each bead is what's output in the `structure.csv` file in the output. When using the `hic2structure` module, calling the `find_contacts` function on a timestep of the LAMMPS results will return a similarly "binary" contact map, consisting of all the pairs of beads whose distance from eachother (in 3D space) is less than the provided threshold (set the `distance_threshold` field in the settings dict).
