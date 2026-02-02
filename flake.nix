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

            # Python packages
            pkgs.python313
            pkgs.python313Packages.python-dotenv
            pkgs.python313Packages.flask
            pkgs.python313Packages.flask-wtf
            pkgs.python313Packages.flask-sqlalchemy
            pkgs.python313Packages.flask-migrate
            pkgs.python313Packages.flask-login
          ];
        };
      }
    );
}
