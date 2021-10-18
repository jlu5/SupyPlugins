import unittest
from parsebird import parse_bird, BirdRouteResult, BirdParseError

class ParseBirdRouteTestCase(unittest.TestCase):
    maxDiff = None

    def testShowRouteBGP(self):
        s = """Table master4:
172.20.0.53/32       unicast [jrb0001 2021-10-06 from fe80::119] * (100) [AS4242420119i]
	via 172.20.1.10 on dn42sea-jrb0001
	Type: BGP univ
	BGP.origin: IGP
	BGP.as_path: 4242420119
	BGP.next_hop: 172.20.1.10
	BGP.local_pref: 300
	BGP.community: (64511,1) (64511,24) (64511,34)
	BGP.large_community: (4242420119, 2000, 10) (4242421080, 101, 44) (4242421080, 103, 114)
"""
        self.assertEqual(
            BirdRouteResult(
                prefix="172.20.0.53/32",
                protocol_name="jrb0001",
                route_preference="100",
                route_type="unicast",
                route_origin="BGP univ",
                via="via 172.20.1.10 on dn42sea-jrb0001",
                bgp_as_path=["4242420119"],
                bgp_community="(64511,1) (64511,24) (64511,34)",
                bgp_large_community="(4242420119, 2000, 10) (4242421080, 101, 44) (4242421080, 103, 114)"
            ), parse_bird(s)
        )

    def testShowRouteBGP6(self):
        s = """Table master6:
fd42:1145:1419:5::/64 unicast [ibgp_us_lax01 03:41:43.904 from fd86:bad:11b7:22::1] * (100/21) [AS4242422464i]
	via fe80::122 on igp-us-lax01
	Type: BGP univ
	BGP.origin: IGP
	BGP.as_path: 4242421288 4242421306 4242421331 4242422464
	BGP.next_hop: fd86:bad:11b7:22::1
	BGP.local_pref: 150
	BGP.community: (64511,1) (64511,24) (64511,33) (64511,44)
	BGP.large_community: (207268, 1, 44) (4242421080, 101, 44) (4242421080, 103, 122) (4242422464, 1, 500)"""

        self.assertEqual(
            BirdRouteResult(
                prefix="fd42:1145:1419:5::/64",
                protocol_name="ibgp_us_lax01",
                route_preference="100/21",
                route_type="unicast",
                route_origin="BGP univ",
                via="via fe80::122 on igp-us-lax01",
                bgp_as_path=['4242421288', '4242421306', '4242421331', '4242422464'],
                bgp_community="(64511,1) (64511,24) (64511,33) (64511,44)",
                bgp_large_community="(207268, 1, 44) (4242421080, 101, 44) (4242421080, 103, 122) (4242422464, 1, 500)"
            ), parse_bird(s)
        )

    def testShowStaticUnreachable(self):
        s = """Table master4:
172.22.108.0/26      unreachable [static1 2021-09-23] * (200)
	Type: static univ
"""
        self.assertEqual(
            BirdRouteResult(
                prefix="172.22.108.0/26",
                protocol_name="static1",
                route_preference="200",
                route_type="unreachable",
                route_origin="static univ"
            ), parse_bird(s)
        )

    def testShowRouteBabel6(self):
        s = """Table master6:
fd86:bad:11b7:53::1/128 unicast [int_babel 20:04:48.769] * (130/18) [00:00:00:00:ac:14:e5:7a]
	via fe80::122 on igp-us-lax01
	Type: Babel univ
	Babel.metric: 18
	Babel.router_id: 00:00:00:00:ac:14:e5:7a
"""
        self.assertEqual(
            BirdRouteResult(
                prefix="fd86:bad:11b7:53::1/128",
                protocol_name="int_babel",
                route_preference="130/18",
                route_type="unicast",
                route_origin="Babel univ",
                via="via fe80::122 on igp-us-lax01"
            ), parse_bird(s)
        )

    def testNetworkNotFound(self):
        s = "Network not found"
        self.assertRaises(BirdParseError, lambda: parse_bird(s))

    def testSyntaxError(self):
        s = "syntax error, unexpected CF_SYM_UNDEFINED, expecting IP4 or IP6 or VPN_RD or CF_SYM_KNOWN"
        self.assertRaises(BirdParseError, lambda: parse_bird(s))

if __name__ == '__main__':
    unittest.main()
