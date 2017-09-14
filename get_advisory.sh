#!/bin/bash

set -e

[ $# -eq 1 ]

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

mkdir -p advisory-tmp
pushd advisory-tmp >/dev/null

advisory=advisory-$xsa.txt
metadata=xsa$xsa.meta
wget_file $advisory
check_sig $advisory
if wget_file $metadata; then
  check_file $advisory $metadata
  for patch in $($TOPDIR/lib/advisory_meta.py $metadata 4.8); do
    wget_file $patch
    check_file $advisory $patch
  done
else
  echo "No metadata, please read the advisory: advisory-tmp/$advisory"
fi
