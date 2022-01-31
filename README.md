# 3D Structure

An adaptation of [this Google Colab Notebook](https://colab.research.google.com/drive/1V4CRdM_hOt4KcM7jBFWjQ6NQyWxECim3?usp=sharing#scrollTo=jftgNJG89Fk9) for processing Hi-C data files. It has been restructured to work as a command-line script.

## Setup

1. Set up your Python virtual environment
```sh
virtualenv venv/
source venv/bin/activate
pip3 install -r requirements.txt
```

2. Install [LAMMPS](https://www.lammps.org/). You may be able to install it with your distro's package manager, or you can download and build it from source.

## Run

```sh
python3 src/hic2structure.py --verbose HIC_FILE
```

This will load contact records from the given Hi-C file and run a LAMMPS simulation on in the directory `./lammps_dir`, creating an output structure data file and contact map file in the directory `./out`. You can override the various default settings with command-line argumnents. Run `python3 src/hic2structure.py --help` to see the available options.
