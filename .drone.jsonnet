# Pipeline template
local test_with(version, use_network=false) = {
    kind: "pipeline",
    type: "docker",
    name: "py" + version + (if use_network then '-online' else ''),
    steps: [
        {
            name: "test",
            image: "python:" + version + "-buster",
            commands: [
                "pip install -r requirements.txt",
                "apt-get update",
                # For SysDNS
                "apt-get -yy install bind9-host",
                "./tests-wrapper.sh" + if !use_network then ' --no-network' else ''
            ],
            failure: if use_network then "ignore",
            environment: {
                [secret_name]: {
                    from_secret: secret_name
                }
                for secret_name in [
                    "AQICN_APIKEY",
                    "NUWEATHER_APIKEY_DARKSKY",
                    "NUWEATHER_APIKEY_OPENWEATHERMAP",
                    "NUWEATHER_APIKEY_WEATHERSTACK",
                    "lastfm_apikey",
                ]
            }
        }
    ]
};

[
    test_with("3.6"),
    test_with("3.6", use_network=true),
    test_with("3.7"),
    test_with("3.8"),
    test_with("3.9"),
    test_with("3.9", use_network=true),
]
