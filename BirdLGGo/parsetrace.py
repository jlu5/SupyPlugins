import re
import sys
import subprocess

from dataclasses import dataclass, field

@dataclass
class TraceResult:
    ips: list[str]
    latency: str = field(default=None)
    notes: list[str] = field(default_factory=list)

class TraceParseError(ValueError):
    pass

# bird-lg-go enables DNS lookups and sends one query by default, but we should be a bit more flexible with what we accept
# This will grab IPs from whichever format is used, and report the first latency / error code of the last line if there are multiple queries
_TRACEROUTE_RE = re.compile(r'\s*\d+\s+(?P<line>(?:[^() ]+ \((?P<IPdns>[0-9a-fA-F.:]+)\)|(?P<IPbare>[0-9a-fA-F.:]+)).*?  (?P<latency>[0-9.]+ ms( \![A-Za-z0-9]+)?)|\*)')
def parse_traceroute(text):
    lines = text.strip().splitlines()
    if len(lines) < 2 or not lines[1].lstrip().startswith("1"):
        # Assume error condition if 2nd line doesn't start with "1" (first hop)
        raise TraceParseError(' '.join(lines) or "traceroute returned empty output")
    else:
        ips = []
        notes = []
        latency = None
        for line in lines[1:]:
            if not line.strip():
                continue
            m = _TRACEROUTE_RE.match(line)
            if not m:
                notes.append(line)
                continue
            ips.append(m.group("IPdns") or m.group("IPbare") or m.group("line"))
            latency = m.group("latency")

        # bird-lg-go specific truncation
        if "hops not responding" in ''.join(notes):
            latency = None

        return TraceResult(ips, latency, notes)

if __name__ == '__main__':
    proc = subprocess.run(['traceroute', *sys.argv[1:]], encoding='utf-8', stdout=subprocess.PIPE)
    print(parse_traceroute(proc.stdout))

    if proc.returncode:
        print("traceroute exited with code", proc.returncode)
    sys.exit(proc.returncode)
