
from supybot.setup import plugin_setup

plugin_setup(
    'Wikifetch',
    install_requires=[
        'bs4',
        'mwparserfromhell',
    ],
)
