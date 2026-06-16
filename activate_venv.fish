# activate_venv.fish
#
# Source this file from the project directory:
#
#   source activate_venv.fish
#   
# It looks for a virtual environment in:
#   1. ./.venv
#   2. ../.venv
#   3. $HOME/.venv

set -l candidates \
    "$PWD/.venv" \
    "$PWD/../.venv" \
    "$HOME/.venv"

for venv_dir in $candidates
    if test -f "$venv_dir/bin/activate.fish"
        source "$venv_dir/bin/activate.fish"

        echo "Activated virtual environment:"
        echo "  $venv_dir"

        if test -x "$venv_dir/bin/python"
            echo "Python:"
            echo "  "(command "$venv_dir/bin/python" --version)
        end

        return 0
    end
end

echo "No virtual environment found."
echo
echo "Looked in:"
for venv_dir in $candidates
    echo "  $venv_dir"
end
echo
echo "To create a project-specific virtual environment, run:"
echo "  python3 -m venv .venv"
echo
echo "Then activate it with:"
echo "  source activate_venv.fish"

return 1
$venv_dir = ".venv"

source "$venv_dir/bin/activate.fish"
echo "Activated virtual environment:"
echo "  $venv_dir"
