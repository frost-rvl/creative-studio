{
  description = "Flask gallery app for digital creativity projects";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.nodejs
            pkgs.lazygit

            # Python packages
            pkgs.python313
            pkgs.python313Packages.python-dotenv
            pkgs.python313Packages.email-validator
            pkgs.python313Packages.pyjwt
            pkgs.python313Packages.pip
            pkgs.python313Packages.pygame
            pkgs.python313Packages.flask
            pkgs.python313Packages.flask-wtf
            pkgs.python313Packages.flask-sqlalchemy
            pkgs.python313Packages.flask-migrate
            pkgs.python313Packages.flask-login
            pkgs.python313Packages.flask-mail
          ];

          shellHook = ''
            if [! -d .venv]; then
                python -m venv .venv
            fi
            source .venv/bin/activate
            pip install pygbag
          '';
        };
      }
    );
}
