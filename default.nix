with import <nixpkgs> {};
python3Packages.buildPythonPackage {
  pname = "gpufan";
  version = "0.0.1";
  src = ./.;
}
