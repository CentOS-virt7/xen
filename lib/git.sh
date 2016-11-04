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

function git-branch-exists
{
    $arg_parse

    $requireargs branch
    
    git rev-parse --verify $branch >& /dev/null
}
