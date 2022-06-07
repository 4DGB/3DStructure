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
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      with builtins;
      with pkgs;
      with pkgs.python310Packages;
      let

        # Git repo for hic-straw
        straw-repo = fetchGit {
          url="https://github.com/aidenlab/straw";
          rev="bc91874571ecd3a50c80cc42582b14147e500d68"; # Latest commit as of June 7, 2022
        };

        # hic-straw python package
        hic-straw = buildPythonPackage {
            pname = "hic-straw";
            version = "1.3.1";
            src = "${straw-repo}/pybind11_python";
            propagatedBuildInputs = [ pybind11 curl ];
        };

        # Dependencies for hic2structure
        deps = [ hic-straw numpy scipy ];

        # hic2structure python package
        hic2structure = buildPythonPackage {
            pname = "hic2structure";
            version = "0.2";
            src = ./.;
            propagatedBuildInputs = deps;
            doCheck = false;
          };

        # LAMMPS executable
        lammps = stdenv.mkDerivation {
          # Based off June 2022 release
          name = "lammps-220602";
          src = fetchGit {
            url="https://github.com/lammps/lammps";
            rev="ceb9466172398e9a20cb510528b4b17f719c7cf2";
          };
          buildInputs = [ cmake ];
          configurePhase = ''
            mkdir build
            cd build
            cmake ../cmake
            cmake -C ../cmake/presets/basic.cmake ../cmake
          '';
          buildPhase = ''
            cmake --build . --parallel ''${NIX_BUILD_CORES:-1}
          '';
          installPhase = ''
            mkdir -p $out/bin
            cp -t $out/bin lmp
          '';

        };

      in rec {
        # Export packages
        packages = { inherit hic2structure hic-straw lammps; };
        defaultPackage = packages.hic2structure;

        # Development environment
        devShell = mkShell {
          buildInputs = [python310 lammps] ++ deps;
        };
      }
    );
}
