#!/bin/bash

set -e

usage() {
  echo "usage: $0 [XSA number]"
}

if [ $# -ne 1 ] || ! [[ "$1" =~ ^[0-9]+$ ]]; then
  usage
  exit 1
fi

TOPDIR=$(pwd)

xsa="$1"

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
    gpg --status-fd 1 --verify $file \
	    | grep -q "VALIDSIG ${xen_key}" || exit 1
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
  [ "$(wc -l <<<"$sum")" -eq 1 ]
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
      eval patches=($(jq --arg v "$version" --arg tree "$tree" -r '.Recipes[$v].Recipes[$tree].Patches | @sh' $meta))
      for patch in "${patches[@]}"; do
        echo "$patch"
      done
    done
  fi
}


mkdir -p advisory-tmp
pushd advisory-tmp >/dev/null

advisory=advisory-$xsa.txt
metadata=xsa$xsa.meta
wget_file $advisory
check_sig $advisory
if wget_file $metadata; then
  check_file $advisory $metadata
  for p in $(get_list_of_patches $metadata); do
    wget_file $patch
    check_file $advisory $patch
  done
else
  echo "No metadata, please read the advisory: advisory-tmp/$advisory"
fi
