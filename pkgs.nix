#
# Nix derivations for hic2structure and its dependencies
#
{ pkgs }:

let
  # Git repo for hic-straw
  straw-repo = fetchGit {
    url="https://github.com/aidenlab/straw";
    rev="bc91874571ecd3a50c80cc42582b14147e500d68"; # Latest commit as of June 7, 2022
  };

  # hic-straw python package
  hic-straw = { python3, curl }: with python3.pkgs; buildPythonPackage {
    pname = "hic-straw";
    version = "1.3.1";
    src = "${straw-repo}/pybind11_python";
    propagatedBuildInputs = [ pybind11 curl ];
  };

  # Dependencies for hic2structure
  pydeps = { python3 }: with python3.pkgs; [ 
    (pkgs.callPackage hic-straw {inherit python3;})
    numpy scipy 
  ];

  # hic2structure python package
  hic2structure = { python3 }: python3.pkgs.buildPythonPackage {
    pname = "hic2structure";
    version = "0.3";
    src = ./.;
    propagatedBuildInputs = pydeps {inherit python3;};
    doCheck = false;
  };

  # Development shell
  devShell = { mkShell, python3 }: with python3.pkgs; mkShell {
    buildInputs = [ python3 (pkgs.callPackage lammps {}) ] ++ (pydeps {inherit python3;});
  };

  # LAMMPS executable
  lammps = { stdenv, cmake }: stdenv.mkDerivation {
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
in
{
  hic-straw = pkgs.callPackage hic-straw {};
  hic2structure = pkgs.callPackage hic2structure {};
  lammps = pkgs.callPackage lammps {};
  devShell = pkgs.callPackage devShell {};
}
