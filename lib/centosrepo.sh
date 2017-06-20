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

    $requireargs version

    if [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] ; then
	_type="release"
    elif [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+rc[0-9]+$ ]] ; then
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
    #FIXME: Handle 4.8rc3

    $arg_parse

    $requireargs version

    version-type var=type

    case $type in
	"release")
	    _tag="RELEASE-$version"
	    ;;
	"rc")
	    if [[ "$version" =~ (^[0-9]+\.[0-9]+\.[0-9]+)(rc[0-9]+)$ ]] ; then
		_tag="${REMATCH[0]}-${REMATCH[1]}"
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
	info "Creating patchqueue branch"
	info "  ...Checking out $tagbranch"
	git checkout $tagbranch || fail "Checking out branch $tagbranch"
	info "  ...Creating branch"
	stg branch --create $pqbranch || fail "Creating stgit branch"
	info "  Importing patchqueue"
	stg import -M ../../SOURCES/xen-queue.am || fail "Importing patchqueue"
	
    fi
	
}

function import-patches()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    $requireargs XEN_VERSION

    if [[ -z "${args[@]}" ]] ; then
	fail "No patches to import"
    fi

    local pqbranch=centos/pq/$XEN_VERSION

    cd $TOPDIR/UPSTREAM/xen.git || fail "Directory doesn't exist!"

    stg-check

    local p
    for p in "${args[@]}" ; do
	info "Importing patch  $p..."
	stg import -m $p || fail "Importing patch $p"
    done

    info "Patches imported to patchqueue.  Don't forget to sync-patches and bump the release number."
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
    git format-patch --stdout -N  base/$basever > ../../SOURCES/xen-queue.am || fail "Updating patchqueue"

    (cd $TOPDIR;
     ./pqnorm.pl)
}

function sync-patches()
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

function rebase()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    $requireargs XEN_VERSION new

    if [[ "$XEN_VERSION" == "$new" ]] ; then
	info "XEN_VERSION already set to $new, nothing to do"
    fi

    make-tree

    echo $PWD

    local newpq=centos/pq/$new
    if ! git-branch-exists branch=$newpq ; then
	checkout-basebranch version="$new" 
    
	local oldpq=centos/pq/$XEN_VERSION
	info "Checking out $oldpq"
	git checkout $oldpq || fail "Checking out patchqueue"
	info "Creating new patchqueue based on old branch"
	stg branch --clone $newpq || fail "Cloning patchqueue"
	info "Rebasing onto new base branch"
	stg rebase base/$new || fail "Rebasing -- please clean up"
    else
	git checkout $newpq || fail "Checking out new patchqueue"
    fi

    sync-patches-internal basever=$new

    info "Updating XEN_VERSION in sources.cfg"
    sed -i --follow-symlinks "s/XEN_VERSION=.*$/XEN_VERSION=$new/" sources.cfg

    info "Rebase done.  Please update Xen version in SPECS/xen.spec and the changelog."
    # Need to create tarball
}

function get-sources()
{
    . sources.cfg

    

    if [[ -n "$XEN_EXTLIB_FILES" ]] ; then
	$requireargs XEN_EXTLIB_URL
	echo "Checking external sources: "
	for i in $XEN_EXTLIB_FILES ; do
	    echo " checking $i"
	    if [[ ! -e SOURCES/$i ]] ; then
		wget -P SOURCES/ $XEN_EXTLIB_URL/$i || exit 1
	    fi
	done
    fi

}
