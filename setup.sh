#!/usr/bin/env bash


# setup the environment using poetry
# WARNING: This must run in the same directory as the pyproject.toml file

if poetry --version ; then
	echo Poetry installed, initialising...
else
	echo "Poetry isn't installed."
	echo 'Install poetry with pipx? Ensure you have pipx installed. Select [1/2]:'
	select yn in Yes No; do
		case $yn in
			Yes ) pipx install poetry; break;;
			No ) echo "CARP activation aborted"; return;;
		esac
	done
fi


# set directory path to variable
export CARP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "CARP_DIR: $CARP_DIR"

# setup environment variables
export PATH=$CARP_DIR/bin:$PATH

echo "$(<${CARP_DIR}/assets/CARP.txt)"


eval $(poetry env activate)