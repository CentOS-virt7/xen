function sources-from-spec()
{
    perl -ne 'if(/^Version.* ([0-9.]+)$/) { $version=$1; } if(/^Patch[0-9]+: (.*)$/ || /^Source[0-9]+: (.*)$/) { $f=$1; if($f=~/http:.*\/([^\/]+)$/) {$f=$1;} $f=~s/%{version}/$version/; print "$f\n"; }' $TOPDIR/SPECS/xen.spec
}

function clean-sources-find()
{
    # Idea:
    # - Pull all files necessary for build out of the spec file
    #  - Patterns:
    #    PatchNN:
    #    SourceNN:
    #  - Replacements:
    #    - Remove http://* trailers
    #    - replace %{version} with the value in Version:
    # - List all the files in SOURCES
    # - Find the lines listed only once
    #
    # NB that this will also produce files present in the spec file
    # but *not* present in SOURCES.
    
    (sources-from-spec && cd $TOPDIR && ls $TOPDIR/SOURCES) | sort | uniq -u
}

function clean-sources()
{
    clean-sources-find | (cd $TOPDIR/SOURCES; xargs rm)
}

function version-type()
{
    local _type

    $arg_parse

    if [[ -z "$version" ]] ; then
	local version="$XEN_VERSION"
    fi
    
    $requireargs version

    if [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] ; then
	_type="release"
    elif [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+-rc[0-9]+$ ]] ; then
	_type="rc"
    else
	_type="unknown"
    fi

    report-result "$_type"
}

function version-to-tag()
{
    local _tag
    local type

    $arg_parse

    $requireargs version

    version-type var=type

    case $type in
	"release")
	    _tag="RELEASE-$version"
	    ;;
	"rc")
	    if [[ "$version" =~ (^[0-9]+\.[0-9]+\.[0-9]+)(-rc[0-9]+)$ ]] ; then
		_tag="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
	    else
		fail "Couldn't parse version"
	    fi
	    ;;
	"unknown")
	    fail "Can't parse version: $version"
	    ;;
    esac

    report-result "$_tag"
}

function version-is-release()
{
    local type
    version-type var=type

    [[ "$type" == "release" ]]
}

function checkout-basebranch()
{
    $arg_parse

    $requireargs version

    local branch=base/$version
    if ! git-branch-exists ; then
	local tag
	version-to-tag var=tag
	info "Creating base branch $branch for tag $tag"
	echo git checkout -b $branch $tag 
	git checkout -b $branch $tag || fail "Creating branch"
    else
	info "Checking out base branch $branch"
	git checkout $branch || fail "Checking out branch"
    fi
    
}

help-add "make-tree: Make UPSTREAM/xen.git and create branches based on SOURCES/xen-queue.am"
function make-tree()
{
    . $TOPDIR/sources.cfg

    $arg_parse
    
    $requireargs XEN_VERSION

    if [[ ! -d UPSTREAM ]] ; then
	info "Creating UPSTREAM/ to store upstream repositories..."
	mkdir UPSTREAM
    fi

    cd UPSTREAM

    if [[ ! -e xen.git ]] ; then
	$requireargs XEN_URL
	info "Cloning xen.git..."
	git clone $XEN_URL xen.git || fail "Cloning xen.git"
	info "done."
	
	cd xen.git
    else
	cd xen.git
	info "Fetching updates to xen.git..."
	git fetch
    fi

    checkout-basebranch version=$XEN_VERSION

    # Now 
    # centos/pq/$version
    local pqbranch=centos/pq/$XEN_VERSION
    if git-branch-exists branch=$pqbranch ; then
	git checkout $pqbranch
    else
	info "Creating patchqueue branch $pqbranch"
	stg branch --create $pqbranch || fail "Creating stgit branch"
	info "  Importing patchqueue"
	stg import -M ../../SOURCES/xen-queue.am || fail "Importing patchqueue"
	
    fi
	
}

help-add "import-patches [patches]: Add patches to the patchqueue for the current version"
function import-patches()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    $requireargs XEN_VERSION

    if [[ -z "${args[@]}" ]] ; then
	fail "No patches to import"
    fi

    local original_dir="$(pwd)"

    local pqbranch=centos/pq/$XEN_VERSION

    pushd >/dev/null $TOPDIR/UPSTREAM/xen.git || fail "Directory doesn't exist!"

    stg-check

    local p
    for p in "${args[@]}" ; do
        if [ "${p:0:1}" != '/' ]; then
            # If path is relative, add original path
            p="$original_dir/$p"
        fi
	info "Importing patch  $p..."
	stg import -m "$p" || fail "Importing patch $p"
    done

    info "Patches imported to patchqueue.  Don't forget to sync-queue and bump the release number."
    popd >/dev/null
}

function sync-patches-internal()
{
    $arg_parse

    # If basever is not specified, get it from the current branch name
    if [[ -z "$basever" ]] ; then
	local lbranch
	local basever
	
	git-get-branch var=lbranch
	basever=$(basename $lbranch)
    fi
    
    info "Exporting patchqueue"
    git format-patch --stdout -N --stat-width=80 base/$basever > ../../SOURCES/xen-queue.am || fail "Updating patchqueue"

    (cd $TOPDIR;
     ./pqnorm.pl)
}

help-add "sync-queue: Update SOURCES/xen-queue.am based on UPSTREAM/xen.git branch"
function sync-queue()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    $requireargs XEN_VERSION

    local pqbranch=centos/pq/$XEN_VERSION

    cd $TOPDIR/UPSTREAM/xen.git || fail "Directory doesn't exist!"

    git checkout $pqbranch || fail "Can't check out patchqueue branch!"

    stg-check

    sync-patches-internal
}

help-add "sync-tree: Update UPSTREAM/xen.git based on SOURCES/xen-queue.am"
function sync-tree()
{
    . $TOPDIR/sources.cfg

    $arg_parse
    
    $requireargs XEN_VERSION

    cd $TOPDIR/UPSTREAM/xen.git || fail "Cannot cd to UPSTREAM/xen.git"

    info "Fetching updates to xen.git..."
    git fetch

    info "Checking out base branch for $XEN_VERSION"
    checkout-basebranch version=$XEN_VERSION

    info "  ...Deleting old pq tree (if any)"
    local pqbranch=centos/pq/$XEN_VERSION
    stg branch --delete --force $pqbranch

    info "  ...Creating branch"
    stg branch --create $pqbranch || fail "Creating stgit branch"
    info "  Importing patchqueue"
    stg import -M ../../SOURCES/xen-queue.am || fail "Importing patchqueue"
}

# Parse the special status string from gpg, depending on the key size
# see gpg --status-fd
function check-gpg-status() {
    $arg_parse
    $requireargs key

    local gpg_status_code
    case "${#key}" in
        16)
            gpg_status_code=GOODSIG
            ;;
        40)
            gpg_status_code=VALIDSIG
            ;;
        *)
            fail "gpg key size incorrect"
            ;;
    esac
    grep -Eq "^\[GNUPG:\] $gpg_status_code $key" ||
        fail "signature check failed ${what:+for }$what"
}

function get-xen-stable() {
    $arg_parse
    $requireargs XEN_VERSION XEN_URL XEN_CSET

    local tag
    version-to-tag version="$XEN_VERSION" var=tag

    local spec_file="$TOPDIR/SPECS/xen.spec"

    local nb_commit=$(perl -ne 'if(/^%define nb_commit ([0-9]+)$/) { print "$1\n";}' "$spec_file")
    local cset_abbrev=${XEN_CSET:0:10}
    local xen_file
    if [ "$nb_commit" -gt 0 ]; then
        xen_file="xen-$tag-$nb_commit-g${cset_abbrev}.tar.gz"
    else
        xen_file="xen-$tag.tar.gz"
        # In this case, the commit id isn't part of the filename, we need to
        # compare the one in sources.cfg and in xen.spec
        local spec_abbrev=$(perl -ne 'if(/^%define abbrev_cset ([0-9a-f]+)$/) { print "$1\n";}' "$spec_file")
        if [ "$cset_abbrev" != "$spec_abbrev" ]; then
            xen_file="we_do_need_to_generate_a_new_tarball"
        fi
    fi

    if [[ ! -e "$TOPDIR/SOURCES/$xen_file" ]] ; then
        pushd "$TOPDIR"

        make-tree

        cd "$TOPDIR/UPSTREAM/xen.git"

        # Have `git describe` always print the same string for a given commit
        git config core.abbrev 10

        # Verify the signature of the expected tag for the current release
        if gpg --list-keys 0x${XEN_KEY} &>/dev/null; then
            if ! git-check-version git_ver=2.6; then
                info "Skip checking tag signature, this requires git 2.6 or newer"
            else
                local gpg_status=$(git verify-tag --raw $tag 2>&1)
                local what="Xen git tag $tag"
                check-gpg-status key=$XEN_KEY <<<"$gpg_status"
            fi
        else
            info "Not checking gpg signature due to missing key; add with gpg --recv-keys ${XEN_KEY}"
        fi

        # By using merge --ff-only after checking out the tag, we make sure we
        # have at least the release tag of $XEN_VERSION in the history of
        # commit id $XEN_CSET.
        git checkout --detach $tag || fail "checkout"
        git merge --ff-only "$XEN_CSET" || fail "fast-forward merge"

        # make src-tarball will use git describe for the tarball name
        xen_file="xen-$(git describe).tar.gz"
        # Allow to run src-tarball without running ./configure first
        touch config/Tools.mk
        make src-tarball || fail "make src-tarball failed"
        mkdir -p "$TOPDIR/SOURCES"
        mv dist/$xen_file $TOPDIR/SOURCES/ || fail "failed to move tarball to SOURCES dir"
        # Update commit count as nb_commit is outdated
        nb_commit="$(git rev-list --count $tag..HEAD)"

        info "Updating nb_commit and abbrev_cset in xen.spec"
        sed -i --follow-symlinks "s/\(%define abbrev_cset \).*$/\1$cset_abbrev/" "$spec_file" || fail "Updating abbrev_cset"
        sed -i --follow-symlinks "s/\(%define nb_commit \).*$/\1$nb_commit/" "$spec_file" || fail "Updating nb_commit"

        popd
    fi
}

help-add "get-sources: Download and/or create tarballs for SOURCES based on sources.cfg"
function get-sources()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    $requireargs XEN_VERSION

    local vtype
    version-type var=vtype

    if [ "$XEN_CSET" ]; then
        # Do a release based on a stable commit
        get-xen-stable
    else
        echo "Checking Xen $XEN_VERSION release tarball"
        if [[ ! -e $TOPDIR/SOURCES/$XEN_RELEASE_FILE ]] ; then
            local url
            case "$vtype" in
                release|rc)
                    url="$XEN_RELEASE_BASE/$XEN_VERSION/$XEN_RELEASE_FILE"
                    ;;
                *)
                    fail "Don't know how to get xen tarball for version $XEN_VERSION (type $vtype)"
                    ;;
            esac
            wget -P $TOPDIR/SOURCES/ "$url" || exit 1
        fi

        if gpg --list-keys 0x${XEN_KEY}; then
            if [[ ! -e $TOPDIR/SOURCES/$XEN_RELEASE_FILE.sig ]]; then
                wget -P $TOPDIR/SOURCES/ $XEN_RELEASE_BASE/$XEN_VERSION/$XEN_RELEASE_FILE.sig || exit 1
            fi
            local gpg_status=$(gpg --status-fd 1 --verify $TOPDIR/SOURCES/$XEN_RELEASE_FILE.sig $TOPDIR/SOURCES/$XEN_RELEASE_FILE)
            local what="Xen release tarball $XEN_RELEASE_FILE"
            check-gpg-status key=${XEN_KEY}  <<<"$gpg_status"
        else
            echo "Not checking gpg signature due to missing key; add with gpg --recv-keys ${XEN_KEY}"
        fi
    fi
    
    if [[ -n "$XEN_EXTLIB_FILES" ]] ; then
	$requireargs XEN_EXTLIB_URL
	echo "Checking external sources: "
	for i in $XEN_EXTLIB_FILES ; do
	    echo " checking $i"
	    if [[ ! -e $TOPDIR/SOURCES/$i ]] ; then
		wget -P $TOPDIR/SOURCES/ $XEN_EXTLIB_URL/$i || exit 1
	    fi
	done
    fi

    echo "Checking blktap..."
    if [[ ! -e $TOPDIR/SOURCES/$BLKTAP_FILE ]] ; then
	mkdir -p $TOPDIR/git-tmp
	pushd $TOPDIR/git-tmp
	
	echo " Cloning blktap repo..."
	git clone $BLKTAP_URL blktap.git || exit 1
	cd blktap.git
	echo " Creating $BLKTAP_FILE..."
	git archive --prefix=blktap2/ -o $TOPDIR/SOURCES/$BLKTAP_FILE $BLKTAP_CSET || exit 1
	popd
    fi

    echo "Checking edk2 (tianocore)..."
    if [[ ! -e $TOPDIR/SOURCES/$EDK2_FILE ]] ; then
	echo "Cloning tianocore repo..."
	mkdir -p $TOPDIR/git-tmp
	pushd $TOPDIR/git-tmp
	
	git clone $EDK2_URL edk2.git || exit 1
	cd edk2.git
	echo "Creating $EDK2_FILE..."
	git archive --prefix=edk2/ -o $TOPDIR/SOURCES/$EDK2_FILE $EDK2_CSET || exit 1
	popd
    fi

    echo "Checking livepatch-build-tools..."
    if [[ -n "$LIVEPATCH_FILE" && ! -e $TOPDIR/SOURCES/$LIVEPATCH_FILE ]] ; then
	echo "Cloning livepatch-build-tools repo..."
	mkdir -p $TOPDIR/git-tmp
	pushd $TOPDIR/git-tmp
	
	git clone $LIVEPATCH_URL livepatch-build-tools.git || exit 1
	cd livepatch-build-tools.git
	echo "Creating $LIVEPATCH_FILE..."
	git archive --prefix=livepatch-build-tools/ -o $TOPDIR/SOURCES/$LIVEPATCH_FILE $LIVEPATCH_CSET || exit 1
	popd
    fi

    if [[ -e $TOPDIR/git-tmp ]] ; then
	echo "Cleaning up cloned repositores"
	rm -rf $TOPDIR/git-tmp
    fi

    echo "All sources present."
}

help-add "rebase new=[new version]: Rebase the patchqueue for the current release onto new-release"
function rebase()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    default continue "false"; $default_post

    $requireargs XEN_VERSION new

    if [[ "$XEN_VERSION" == "$new" ]] ; then
	info "XEN_VERSION already set to $new, nothing to do"
    fi

    make-tree

    echo $PWD

    local newpq=centos/pq/$new

    checkout-basebranch version="$new"

    if git-branch-exists branch=$newpq ; then
	stg branch --delete --force $newpq
    fi
    
    local oldpq=centos/pq/$XEN_VERSION
    
    info "Checking out $oldpq"
    git checkout $oldpq || fail "Checking out patchqueue"

    info "Creating new patchqueue based on old branch"
    stg branch --clone $newpq || fail "Cloning patchqueue"

    info "Finding duplicate patches to remove from the queue"
    
    info " ...Finding patch-id's of current patches in the series"
    local series_pids
    stg-get-patch-ids var=series_pids

    local from
    local to
    local upstream_pids
    version-to-tag var=from version="$XEN_VERSION"
    version-to-tag var=to version="$new"
    info " ...Finding patch-id's of commits between $from and $to"
    # Inherits 'from' and 'to'
    git-get-patch-ids var=upstream_pids

    info " ...Finding duplicate patch-id's"
    local dups
    # Inherits series_pids and upstream_pids
    find-duplicate-patch-ids var=dups

    info " ...Removing duplicate patches"
    stg pop -a
    if [ -n "$dups" ]; then
        stg delete $dups || fail "Removing patches $dups"
    fi

    info "Rebasing onto new base branch"
    stg rebase base/$new || fail "Rebasing -- please clean up and run rebase-post"
    stg push -a || fail "Rebasing -- please clean up and run rebase-post"

    rebase-post
}

help-add "rebase-post: Finish off a partially-completed rebase"
function rebase-post()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    pushd $TOPDIR/UPSTREAM/xen.git

    if [[ -z "$new" ]] ; then
	local new
	local lbranch
	
	git-get-branch var=lbranch
	
	new=$(basename $lbranch)
    fi

    $requireargs XEN_VERSION

    stg clean || fail "Cleaning patchqueue"

    sync-patches-internal basever=$new

    if [ "$XEN_CSET" ]; then
        local new_id=$(git log --format=format:%H -1 "$new^{commit}")
    fi

    popd

    info "Updating XEN_VERSION in sources.cfg"
    sed -i --follow-symlinks "s/XEN_VERSION=.*$/XEN_VERSION=$new/" $TOPDIR/sources.cfg || fail "Updating XEN_VERSION"
    if [ "$XEN_CSET" ]; then
        sed -i --follow-symlinks "s/^\(XEN_CSET=\).*$/\1$new_id/" $TOPDIR/sources.cfg || fail "Updating XEN_CSET"
    fi
    info "Updating SPECS/xen.spec (hv_abi, xen_version, xen_rc_base)"
    if [[ "$new" =~ (^[0-9]+\.[0-9]+)(\.[0-9]+)(-(rc[0-9]+))?$ ]] ; then
        local spec_file="$TOPDIR/SPECS/xen.spec"
        sed -i -E -e "s/^(%define hv_abi\s).*/\1${BASH_REMATCH[1]}/" \
            -e "s/^(%define xen_version %\{hv_abi\})\.[0-9]+$/\1${BASH_REMATCH[2]}/" \
            -e "s/^(%define xen_rc_base\s).*$/\1${BASH_REMATCH[4]:-0}/" \
            "$spec_file"
    else
        fail "Couldn't parse version"
    fi

    get-sources # NB at this point XEN_VERSION will change

    info "Rebase done.  Please update Xen version in SPECS/xen.spec and the changelog."
}

# Check one patch to see if it's been checked in upstream (to be used during a rebase)
function stg-check-patch-one()
{
    $arg_parse

    $requireargs lastversion
    
    local patchname=$(stg series --noprefix --unapplied | head -1)

    if [[ -z "$patchname" ]] ; then
	info "No more patches"
	return 0
    fi

    info "Next patch: $patchname"

    stg export --stdout $patchname > /tmp/series-next.patch

    oneline=$(head -1 /tmp/series-next.patch)

    info "Description: $oneline"

    gitlog=$(git log --oneline --decorate= --grep="$oneline" RELEASE-$lastversion..)

    if [[ -z "$gitlog" ]] ; then
	info "Can't find patch in log, applying"
	stg push
	return
    fi

    local cs
    if [[ $gitlog =~ ^([0-9a-f]+)\  ]] ; then
	cs=${BASH_REMATCH[0]}
	info "Candidate changeset: $cs"
    else
	fail "Couldn't parse gitlog ($gitlog)!"
    fi

    # Check the patch ID
    git format-patch -1 --stdout $cs > /tmp/candidate.patch

    seriesid=$(git patch-id < /tmp/series-next.patch | awk '{print $1;}')
    candidateid=$(git patch-id < /tmp/candidate.patch | awk '{print $1;}')

    if [[ $seriesid != $candidateid ]] ; then
	echo "WARNING: seriesid $seriesid != candidateid $candidateid, Check to make sure commit $oneline actually exists"
    fi

    info "Deleting patch $patchname"

    stg delete $patchname
}
