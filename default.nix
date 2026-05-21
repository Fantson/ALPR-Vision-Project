{
  pkgs ? import <nixpkgs> { },
}:
with pkgs;
mkShell {
  packages = [
    (python3.withPackages (
      python-pkgs: with python-pkgs; [
        opencv4
        numpy
        pytesseract
      ]
    ))
    tesseract

    typst
    typstyle
  ];

  shellHook = ''
    unset SOURCE_DATE_EPOCH
  '';
}
