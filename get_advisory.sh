#!/bin/bash

set -e

trap 'echo Failed to execute "$BASH_COMMAND" with $? at $LINENO' ERR

usage() {
  echo "usage: $0 [XSA number]"
}

if [ $# -lt 1 ] || ! [[ "$1" =~ ^[0-9]+$ ]]; then
  usage
  exit 1
fi

TOPDIR=$(pwd)

xsa="$1"; shift

error_exit() {
  echo >&2 "$@"
  exit 1
}

wget_file(){
  local url="https://xenbits.xen.org/xsa"
  local file="$1"
  mkdir -p "$(dirname "$file")"
  wget --quiet -O "$file" "$url/$file"
}

check_sig(){
  local xen_key='23E3222C145F4475FA8060A783FE14C957E82BD9'
  local file="$1"

  if gpg --list-keys ${xen_key} >/dev/null; then
    if ! gpg --status-fd 1 --verify $file \
	    | grep -q "VALIDSIG ${xen_key}"; then
      error_exit "Failed to check signature of '$file'"
      return 1
    fi
  else
    echo >&2 -n "Not checking gpg signature due to missing key;"
    echo >&2 "add with gpg --recv-keys ${xen_key}"
  fi
}

extract_sha256sum(){
  sed -n '/^\$ sha256sum/{:next; n; /^\$$/b; p; b next}' "$1"
}
check_file(){
  local advisory="$1"
  local file="$2"

  sums="$(extract_sha256sum $advisory)"
  sum="$(grep -E "^[0-9a-f]+  $file$" <<<"$sums")"
  [ -n "$sum" ] || return 1
  [ "$(wc -l <<<"$sum")" -eq 1 ] || return 1
  sha256sum -c <<<"$sum"
}

get_list_of_patches(){
  # Using jq
  local meta="$1"
  local version='4.8'
  local tree
  local trees
  local has_patch=$(jq --arg v "$version" -r '.SupportedVersions | contains([$v]) | @sh' $meta)
  if $has_patch; then
    eval trees=($(jq -r '.Trees | @sh' $meta))
    for tree in "${trees[@]}"; do
      jq --arg v "$version" --arg tree "$tree" -r '.Recipes[$v].Recipes[$tree].Patches | @sh' $meta
    done
  fi
}

get_patches_list_from_advisory(){
  local advisory="$1"
  local glob="$2"
  local sums
  local -a patches

  if [[ "$glob" =~ ^[^/]+/\*$ ]]; then
    sums="$(extract_sha256sum $advisory)"
    glob="${glob%/\*}"
    IFS='
'
    patches=($(sed -rn "s%^[0-9a-f]+  ($glob/.*)$%\1%p" <<<"$sums"))
  elif [[ "$glob" =~ ^[^/]+/\*\.patch$ ]]; then
    sums="$(extract_sha256sum $advisory)"
    glob="${glob%/\*.patch}"
    IFS='
'
    patches=($(sed -rn "s%^[0-9a-f]+  ($glob/.*\.patch)$%\1%p" <<<"$sums"))
  else
    patches=("$glob")
  fi
  unset IFS
  for p in "${patches[@]}"; do
    echo -n " '$p'"
  done
}


mkdir -p advisory-tmp
pushd advisory-tmp >/dev/null

advisory=advisory-$xsa.txt
metadata=xsa$xsa.meta
wget_file $advisory
check_sig $advisory
to_import=()
if [ $# -ge 1 ]; then
  # Hack for XSA240-v5, which have no metadata but v4 had

  for patch in "$@"; do
    # Check if "Patches" in the metadata are in a globing format
    # if not, the function just return $patch unchanged
    eval patch=($(get_patches_list_from_advisory $advisory "$patch"))
    for patch in "${patch[@]}"; do
      if ! wget_file "$patch"; then
        error_exit "Unable to download patch $patch"
      fi
      if ! check_file $advisory "$patch"; then
        error_exit "Failed to check patch '$patch'"
      fi
      to_import+=("$patch")
    done
  done
  echo "Done checking patchs: ${to_import[@]}"
elif wget_file $metadata; then
  if ! check_file $advisory $metadata; then
    error_exit "Failed to check metadata file ($metadata)"
  fi
  eval patches=($(get_list_of_patches $metadata))
  for patch in "${patches[@]}"; do
    # Check if "Patches" in the metadata are in a globing format
    # if not, the function just return $patch unchanged
    eval patch=($(get_patches_list_from_advisory $advisory "$patch"))
    for patch in "${patch[@]}"; do
      if ! wget_file "$patch"; then
        error_exit "Unable to download patch $patch"
      fi
      if ! check_file $advisory "$patch"; then
        error_exit "Failed to check patch '$patch'"
      fi
      to_import+=("$patch")
    done
  done
  echo -n "Import patches ? ${to_import[@]} [yN] "
  read answer
  if [[ "$answer" =~ ^[Yy]$ ]]; then
    ../repo import-patches "${to_import[@]}"
  fi
else
  echo "No metadata, please read the advisory: advisory-tmp/$advisory"
fi
