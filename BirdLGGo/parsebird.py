import re

from dataclasses import dataclass, field
from typing import List

@dataclass
class BirdRouteResult:
    prefix: str
    protocol_name: str
    route_preference: str
    route_type: str

    route_origin: str = field(default=None)
    via: str = field(default=None)
    bgp_as_path: List[str] = field(default_factory=list)
    bgp_community: str = field(default=None)
    bgp_large_community: str = field(default=None)

class BirdParseError(ValueError):
    pass

_ROUTE_INFO_RE = re.compile(r'(?P<prefix>[0-9a-fA-F.:]+\/[0-9]+).*?(?P<type>[a-z]+) \[(?P<protocol_name>\w+).*?\] \* \((?P<preference>.*?)\)')
def parse_bird(text):
    """
    Return details of the first route in bird's "show route ... all" output.

    This is most useful if you specify a query that only returns one route - e.g. by writing "show route ... primary all"
    """
    text = text.strip()
    lines = text.splitlines()
    if not text.startswith("Table"):
        # Unexpected format - probably an error like "Route not found"
        raise BirdParseError(text)
    if len(lines) < 3:
        raise BirdParseError("Not enough data (expected at least 3 lines, got %d" % len(lines))

    m = _ROUTE_INFO_RE.match(lines[1])
    if not m:
        raise BirdParseError("Failed to match route info against regex")
    result = BirdRouteResult(
        prefix=m.group("prefix"),
        protocol_name=m.group("protocol_name"),
        route_preference=m.group("preference"),
        route_type=m.group("type"),
        # Most routes except unreachable etc. should specify an interface or IP next hop.
        # For unreachable routes, this seems to fall back to a "Type:" field instead
        via=None if "Type:" in lines[2] else lines[2].strip())

    for line in lines[2:]:
        parts = line.strip().split(" ", 1)
        if parts[0] == "Type:":
            result.route_origin = parts[1]
        if parts[0] == "BGP.as_path:":
            result.bgp_as_path = parts[1].split()
        if parts[0] == "BGP.community:":
            result.bgp_community = parts[1]
        if parts[0] == "BGP.large_community:":
            result.bgp_large_community = parts[1]
    return result
