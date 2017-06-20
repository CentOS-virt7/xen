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
