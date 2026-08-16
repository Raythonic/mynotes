#!/bin/bash
git config --global rerere.enabled true || exit 1
git config --global rerere.autoupdate true || exit 1

if [ "${MY_APP_BUILD_SERVER:-}" != "Y" ]
then
    if git show-ref --verify --quiet refs/heads/develop
    then
        git switch develop || exit 1
    elif git show-ref --verify --quiet refs/remotes/origin/develop
    then
        git switch --track -c develop origin/develop || exit 1
    else
        git switch -c develop || exit 1
    fi
    git add . || exit 1

    if ! git diff --cached --quiet
    then
        commit_message="Publish $(basename "$PWD") from ${HOSTNAME:-$(hostname)}"
        [ -s commit.txt ] && commit_message=$(head -n 1 commit.txt)
        git commit -m "$commit_message" || exit 1
    fi

    git push origin develop
    exit $?
fi

. /home/rwalk/bin/publisher

pip freeze > install/requirements.txt
bash scripts/load-mynotes-manpages.sh
publish "$1" || exit 1
