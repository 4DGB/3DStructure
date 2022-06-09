#
# Nix flake for hic2structure package
# 
# This flake brings in and exports a few dependencies, which are available
# through the exported packages. Namely, the hic-straw python package
# from aidenlabs and a copy of LAMMPS with the basic packages enabled
#
{
  description = "Python module for processing Hi-C files through LAMMPS";

  inputs = {
    # Nixpkgs
    nixpkgs.url = "github:NixOS/nixpkgs/release-22.05";

    # Flake-compat library
    # (Used to generate a flake-less nix.shell file)
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };

    # Flake-utils library
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-compat, flake-utils, mach-nix }:
    flake-utils.lib.eachDefaultSystem (system:
      with builtins;
      let
        pkgs = nixpkgs.legacyPackages.${system};
        myPkgs = import ./pkgs.nix { inherit pkgs; };
      in
      rec {
        # Export packages
        packages = { inherit (myPkgs) hic2structure hic-straw lammps; };
        defaultPackage = packages.hic2structure;

        # Development environment
        devShell = myPkgs.devShell;
      }
    );
}
