#!/bin/bash

# Exclude stubs for (re)moved plugins
SKIP_PLUGINS=("--exclude=./Weather" "--exclude=./DDG" "--exclude=./SedRegex")

if [[ -n "$DRONE_PULL_REQUEST" ]]; then
    echo "Skipping tests that require secret API keys"
    export SKIP_PLUGINS+=("--exclude=./LastFM" "--exclude=./NuWeather" "--exclude=./AQI")
fi

supybot-test -c --plugins-dir=. "${SKIP_PLUGINS[@]}" "$@"
