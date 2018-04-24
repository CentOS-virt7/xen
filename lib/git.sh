function stg-apply-mbox()
{
    local f

    $arg_parse

    if [[ -z "$mbox" ]] ; then
	local mbox
	mbox = ${args[0]}
    fi

    [[ -e "$mbox" ]] || fail "Can't find mbox $mbox!\n"

    info "Removing old .rej files"

    find . -name "*.rej" | xargs rm -f

    while ! stg import -M -i --reject $mbox ; do
	for f in $(find . -name "*.rej") ; do
	    emacsclient $f
	    rm -f $f
	done
    done
}

function stg-check()
{
    stg series >& /dev/null || fail "Not on an stg branch"
}

# Returns $patchname,$patchid tuples
# var: Store results in variable 'var'
# branch: Operate on this stg branch (instead of the current one)
function stg-get-patch-ids()
{
    $arg_parse

    local _pname
    local _pid
    local _result
    local branch_arg

    if [[ -n "$branch" ]] ; then
	branch_arg="-b $branch"
    fi
    
    for _pname in $(stg series $branch_arg --noprefix) ; do
	_pid=$(stg sh $branch_arg $_pname | git patch-id --stable | awk '{print $1;}') ;
	if [[ -z "$_result" ]] ; then
	    _result="$_pname,$_pid"
	else
	    _result="$_result $_pname,$_pid"
	fi
    done

    report-result "$_result"
}

# Returns $commitname,$commitid tuples
# from, to: Range to operate on 
# var: Store results in variable 'var'
function git-get-patch-ids()
{
    $arg_parse

    $requireargs from to
    
    local _cid
    local _pid
    local _result

    for _cid in $(git log ${from}..${to} | awk '{print $1;}') ; do
	_pid=$(git sh $_cid | git patch-id --stable | awk '{print $1;}')
	if [[ -z "$_result" ]] ; then
	    _result="$_cid,$_pid"
	else
	    _result="$_result $_cid,$_pid"
	fi
    done

    report-result "$_result"
}

function find-duplicate-patch-ids()
{
    $arg_parse

    $requireargs series_pids upstream_pids
    
    local _result

    # Change space to newline, comma to space
    _result=$((for i in $upstream_pids $series_pids ; do echo ${i/,/ } ; done ) |
		  sort -k 2 -r |
		  uniq -f 1 -d |
		  awk '{print $1}')

    report-result "$_result"
}

function git-branch-exists
{
    $arg_parse

    $requireargs branch
    
    git rev-parse --verify $branch >& /dev/null
}

function git-get-branch
{
    $arg_parse
    
    local _branch=$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)

    report-result "$_branch"
}
