#! /bin/bash -e

if [ ! -d code ]; then
  git clone https://github.com/$WMCORE_REPO/$CODE_REPO.git code
fi

pushd code
git pull --rebase origin $WMCORE_BRANCH
popd
