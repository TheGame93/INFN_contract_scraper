#!/usr/bin/env bash

# Usage:
#   source scripts/setup_venv.sh
#
# This script must be sourced so that `.venv` activation affects the current shell.

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "Run this with: source scripts/setup_venv.sh"
    exit 1
fi

_infn_jobs_setup_venv() {
    local script_dir project_root venv_dir requirements_file

    script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
    project_root="$(cd -- "${script_dir}/.." && pwd)"
    venv_dir="${project_root}/.venv"
    requirements_file="${project_root}/pythonrequirements.txt"

    if ! command -v python3 >/dev/null 2>&1; then
        echo "python3 not found in PATH."
        return 1
    fi
    if [[ ! -f "${requirements_file}" ]]; then
        echo "Requirements file not found: ${requirements_file}"
        return 1
    fi

    if [[ ! -d "${venv_dir}" ]]; then
        echo "Creating virtual environment in ${venv_dir}"
        python3 -m venv "${venv_dir}" || return 1
    fi

    # shellcheck disable=SC1091
    source "${venv_dir}/bin/activate" || return 1

    if [[ "${INFN_JOBS_SKIP_PIP_INSTALL:-0}" == "1" ]]; then
        echo "Skipping pip installations (INFN_JOBS_SKIP_PIP_INSTALL=1)."
    else
        echo "Installing requirements from ${requirements_file}"
        python -m pip install -r "${requirements_file}" || return 1
        echo "Installing project in editable mode"
        python -m pip install -e "${project_root}" || return 1
    fi

    echo "Environment ready. Active Python: $(command -v python)"
}

_infn_jobs_setup_venv || return 1
unset -f _infn_jobs_setup_venv
