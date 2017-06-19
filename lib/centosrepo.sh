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

function get-sources()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    $requireargs XEN_VERSION

    local vtype
    version-type var=vtype

    echo "Checking Xen $XEN_VERSION release tarball"
    if [[ ! -e $TOPDIR/SOURCES/$XEN_RELEASE_FILE ]] ; then
	if [[ "$vtype" != "release" ]] ; then
	    fail "Don't know how to get xen tarball for version $XEN_VERSION (type $vtype)"
	fi
	wget -P $TOPDIR/SOURCES/ $XEN_RELEASE_BASE/$XEN_VERSION/$XEN_RELEASE_FILE || exit 1
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

    if [[ -e $TOPDIR/git-tmp ]] ; then
	echo "Cleaning up cloned repositores"
	rm -rf $TOPDIR/git-tmp
    fi

    echo "All sources present."
}

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
    info "Rebasing onto new base branch"
    stg rebase base/$new || fail "Rebasing -- please clean up and run rebase-post"

    rebase-post
}

function rebase-post()
{
    . $TOPDIR/sources.cfg

    $arg_parse

    cd $TOPDIR/UPSTREAM/xen.git

    if [[ -z "$new" ]] ; then
	local new
	local lbranch
	
	git-get-branch var=lbranch
	
	new=$(basename $lbranch)
    fi

    $requireargs XEN_VERSION

    sync-patches-internal basever=$new

    info "Updating XEN_VERSION in sources.cfg"
    sed -i --follow-symlinks "s/XEN_VERSION=.*$/XEN_VERSION=$new/" $TOPDIR/sources.cfg || fail "Updating XEN_VERSION"

    get-sources # NB at this point XEN_VERSION will change

    info "Rebase done.  Please update Xen version in SPECS/xen.spec and the changelog."
}
