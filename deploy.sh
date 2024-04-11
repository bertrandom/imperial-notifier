#!/bin/bash
rsync -av --exclude-from=.gitignore --exclude .git ./ bertrand@server:/web/imperial-notifier/
scp config/development.json bertrand@server:/web/imperial-notifier/config/development.json
scp config/prod.json bertrand@server:/web/imperial-notifier/config/prod.json
