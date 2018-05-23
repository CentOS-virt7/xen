# vim:sw=4

# Location where downloaded XSAs advisory and patches will be stored
function get-xsa-dir()
{
    $arg_parse
    $requireargs TOPDIR

    local _dir="$TOPDIR/UPSTREAM/XSAs"
    mkdir -p "$_dir" || fail "Failed to create '$_dir'"
    report-result "$_dir"
}

help-add "import-xsa xsa=[XSA]: Download and check a Xen Security Advisory"
function import-xsa()
{
    . $TOPDIR/sources.cfg

    $arg_parse
    $requireargs xsa XEN_VERSION TOPDIR

    local -a patches
    local advisory metadata
    local xen

    local advisory_file="advisory-$xsa.txt"
    local metadata_file="xsa$xsa.meta"

    if [[ "$XEN_VERSION" =~ ^([4-9])\.([1-9][0-9]*)\.[0-9] ]]; then
        xen="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}"
    else
        fail "Unrecognize Xen version $XEN_VERSION from XEN_VERSION"
    fi

    info "Will download advisory / patches in UPSTREAM/XSAs/"

    download-xsa-file file="$advisory_file" || fail "no advisory"
    advisory="$(get-xsa-dir)/$advisory_file"
    xen-check-files-gpg-signature file="$advisory"

    if download-xsa-file file="$metadata_file"; then
        metadata="$(get-xsa-dir)/$metadata_file"
        if ! xsa-check-file-checksum-from-advisory file="$metadata_file"; then
            fail "Failed to check metadata file ($metadata_file)"
        fi

        xsa-extract-patch-list-from-metadata var=patches
    fi

    if [ "${#patches[@]}" -eq 0 ]; then
        fail "No patch found for advisory XSA-$xsa"
    fi

    local patch_glob file
    local -a patches_name
    # Maybe a list of patch, or a list of globbing
    for patch_glob in "${patches[@]}"; do
        xsa-extract-patch-list-from-advisory var=patches_name glob="$patch_glob"
        for file in "${patches_name[@]}"; do
            download-xsa-file || fail "patch $file missing"
            if ! xsa-check-file-checksum-from-advisory; then
                fail "Patch $file checksum failed"
            fi
        done
    done
}

# Download XSA file into UPSTREAM/XSAs
function download-xsa-file()
{
    $arg_parse
    $requireargs file

    local url="https://xenbits.xen.org/xsa"
    local dir

    get-xsa-dir var=dir

    mkdir -p "$dir/$(dirname "$file")"

    if ! wget --quiet -O "$dir/$file" "$url/$file"; then
        error "Download of '$file' failed"
        return 1
    fi
}

function xen-check-files-gpg-signature()
{
    $arg_parse
    $requireargs file

    local xen_key='23E3222C145F4475FA8060A783FE14C957E82BD9'

    if gpg --list-keys ${xen_key} >/dev/null; then
        if ! gpg --status-fd 1 --verify "$file" \
	    | grep -q "VALIDSIG ${xen_key}"; then
            fail "Failed to check signature of '$file'"
        fi
    else
        info "Not checking gpg signature due to missing key;"
        info "  add with gpg --recv-keys ${xen_key}"
    fi
}

function xsa-extract-patch-list-from-metadata()
{
    $arg_parse
    $requireargs metadata xen

    local tree
    local trees
    local has_patch=$(jq --arg v "$xen" -r '.SupportedVersions | contains([$v]) | @sh' $metadata)
    local -a _patches
    if $has_patch; then
        eval trees=($(jq -r '.Trees | @sh' $metadata))
        for tree in "${trees[@]}"; do
            # TODO: What happen if there is more than one tree, and it's not xen?
            [[ $tree = xen ]] || fail "Metadata contain patches for trees other then xen, please check script."
            eval _patches=($(jq --arg v "$xen" --arg tree "$tree" -r '.Recipes[$v].Recipes[$tree].Patches | @sh' $metadata))
        done
    else
        fail "XSA don't have patch for Xen $xen"
    fi

    report-result-array "${_patches[@]}"
}

function xsa-extract-checksum-list-from-advisory()
{
    $arg_parse
    $requireargs advisory

    local _list
    _list=$(sed -n '/^\$ sha256sum/{:next; n; /^\$$/b; p; b next}' "$advisory")

    report-result "$_list"
}

# Extract checksum of a file from an advisory, and check that file's checksum
function xsa-check-file-checksum-from-advisory()
{
    $arg_parse
    $requireargs advisory file

    local sums sum
    xsa-extract-checksum-list-from-advisory var=sums

    pushd "$(get-xsa-dir)" >/dev/null || fail "cd '$(get-xsa-dir)'"

    sum="$(grep -E "^[0-9a-f]+  $file$" <<<"$sums")"
    [ -n "$sum" ] || return 1
    [ "$(wc -l <<<"$sum")" -eq 1 ] || return 1
    sha256sum -c <<<"$sum" || return 1

    popd >/dev/null
}

# advisory: location of the advisory file
# glob: Some string found in XSAs describing which patch applies to a
#       particular version of Xen
#       This may be a filename or a string in globbing format
function xsa-extract-patch-list-from-advisory()
{
    $arg_parse
    $requireargs advisory glob

    local checksums
    local -a _patches

    xsa-extract-checksum-list-from-advisory var=checksums

    IFS='
'
    _files=($(sed -r "s%^[0-9a-f]+  %%" <<<"$checksums"))
    unset IFS
    for _file in "${_files[@]}"; do
        # Warning: if glob is xsa42*, this will match file both named:
        # xsa42/001-foo.patch and xsa42-1-bar.patch
        # This test doesn't care for directories like pathname expansion would do.
        if [[ "$_file" == $glob ]]; then
            _patches+=("$_file")
        fi
    done

    report-result-array "${_patches[@]}"
}
