export FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --env-filter '
if [ "$GIT_AUTHOR_EMAIL" = "zaimc@developlus.ai" ]; then
    export GIT_AUTHOR_NAME="Zaim Can"
    export GIT_AUTHOR_EMAIL="zaimcanvayic08@gmail.com"
    export GIT_COMMITTER_NAME="Zaim Can"
    export GIT_COMMITTER_EMAIL="zaimcanvayic08@gmail.com"
fi
' -- --all
