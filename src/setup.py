import setuptools

setuptools.setup(
    name="hic2structure",
    version="0.1",
    description="4D Genome Toolkit.",
    url="https://github.com/4DGB/3DStructure",
    packages=[ "lib", "lib.lammps" ],
    scripts=["hic2structure.py"]
)