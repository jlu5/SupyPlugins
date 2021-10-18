import unittest
from parsetrace import parse_traceroute, TraceResult

class ParseTraceTestCase(unittest.TestCase):
    maxDiff = None

    def testTracerouteSingleQuery(self):
        s = """traceroute to ipv6.google.com (2607:f8b0:4009:809::200e), 30 hops max, 80 byte packets
 1  2605:4840:3::1 (2605:4840:3::1)  1.269 ms
 2  2604:6600:2700:11::1 (2604:6600:2700:11::1)  0.442 ms
 3  ce-0-7-0-2.r07.chcgil09.us.bb.gin.ntt.net (2001:418:0:5000::ec0)  1.083 ms
 4  eqix-ch-200g-1.google.com (2001:504:0:4:0:1:5169:1)  62.029 ms
 5  *
 6  2001:4860:0:1::5737 (2001:4860:0:1::5737)  0.870 ms
 7  ord37s33-in-x0e.1e100.net (2607:f8b0:4009:809::200e)  46.306 ms
"""
        self.assertEqual(TraceResult(ips=[
            "2605:4840:3::1",
            "2604:6600:2700:11::1",
            "2001:418:0:5000::ec0",
            "2001:504:0:4:0:1:5169:1",
            "*",
            "2001:4860:0:1::5737",
            "2607:f8b0:4009:809::200e"
        ], latency="46.306 ms"), parse_traceroute(s))

    def testTracerouteMultiQuery(self):
        s = """traceroute to 1.1.1.1 (1.1.1.1), 30 hops max, 60 byte packets
 1  205.185.112.1 (205.185.112.1)  0.418 ms  0.360 ms  0.310 ms
 2  172.18.0.29 (172.18.0.29)  0.648 ms  0.517 ms  0.405 ms
 3  100ge3-2.core1.slc1.he.net (184.104.194.81)  20.144 ms  20.177 ms  20.161 ms
 4  cloudflare.slix.net (149.112.13.27)  9.057 ms  9.060 ms  9.504 ms
 5  one.one.one.one (1.1.1.1)  8.567 ms  8.688 ms  8.764 ms
"""
        self.assertEqual(TraceResult(ips=[
            '205.185.112.1',
            '172.18.0.29',
            '184.104.194.81',
            '149.112.13.27',
            '1.1.1.1'
        ], latency="8.567 ms"), parse_traceroute(s))

    def testTracerouteMultiQueryDifferentPaths(self):
        s = """traceroute to google.com (142.250.185.174), 30 hops max, 60 byte packets
 1  172.31.1.1 (172.31.1.1)  5.918 ms  5.974 ms  5.959 ms
 2  17476.your-cloud.host (49.12.142.82)  0.339 ms  0.408 ms  0.405 ms
 3  * * *
 4  static.237.3.47.78.clients.your-server.de (78.47.3.237)  2.441 ms static.233.3.47.78.clients.your-server.de (78.47.3.233)  0.973 ms static.237.3.47.78.clients.your-server.de (78.47.3.237)  2.269 ms
 5  static.85.10.239.169.clients.your-server.de (85.10.239.169)  0.914 ms  0.908 ms  1.246 ms
 6  static.85-10-228-85.clients.your-server.de (85.10.228.85)  2.445 ms core11.nbg1.hetzner.com (85.10.250.209)  1.037 ms core11.nbg1.hetzner.com (213.239.208.221)  0.972 ms
 7  core1.fra.hetzner.com (213.239.245.250)  3.951 ms core0.fra.hetzner.com (213.239.252.25)  3.374 ms core1.fra.hetzner.com (213.239.245.250)  3.497 ms
 8  core8.fra.hetzner.com (213.239.224.217)  9.705 ms  3.626 ms core8.fra.hetzner.com (213.239.245.126)  3.697 ms
 9  142.250.169.172 (142.250.169.172)  3.822 ms  3.587 ms  3.624 ms
10  * * *
11  142.250.226.148 (142.250.226.148)  3.881 ms 142.250.46.248 (142.250.46.248)  3.701 ms 172.253.50.150 (172.253.50.150)  5.400 ms
12  142.250.210.209 (142.250.210.209)  3.812 ms 108.170.252.18 (108.170.252.18)  3.763 ms 142.250.210.209 (142.250.210.209)  3.685 ms
13  fra16s51-in-f14.1e100.net (142.250.185.174)  3.895 ms  3.871 ms  3.945 ms
"""
        self.assertEqual(TraceResult(ips=[
            '172.31.1.1',
            '49.12.142.82',
            '*',
            '78.47.3.237',
            '85.10.239.169',
            '85.10.228.85',
            '213.239.245.250',
            '213.239.224.217',
            '142.250.169.172',
            '*',
            '142.250.226.148',
            '142.250.210.209',
            '142.250.185.174'], latency="3.895 ms"), parse_traceroute(s))

    def testTracerouteTimedOut(self):
        s = """
traceroute to azure.microsoft.com (13.107.42.16), 30 hops max, 60 byte packets
 1  172.31.1.1 (172.31.1.1)  9.411 ms  9.405 ms  9.404 ms
 2  17476.your-cloud.host (49.12.142.82)  0.341 ms  0.189 ms  0.086 ms
 3  * * *
 4  static.237.3.47.78.clients.your-server.de (78.47.3.237)  0.822 ms static.233.3.47.78.clients.your-server.de (78.47.3.233)  0.944 ms  0.876 ms
 5  static.85.10.248.221.clients.your-server.de (85.10.248.221)  0.923 ms  1.164 ms  1.086 ms
 6  core11.nbg1.hetzner.com (213.239.208.221)  0.596 ms  0.449 ms core12.nbg1.hetzner.com (85.10.250.213)  2.050 ms
 7  core5.fra.hetzner.com (213.239.224.238)  3.574 ms core1.fra.hetzner.com (213.239.245.250)  3.480 ms  3.491 ms
 8  ae72-0.fra-96cbe-1b.ntwk.msn.net (104.44.37.193)  3.748 ms hetzner.fra-96cbe-1a.ntwk.msn.net (104.44.197.103)  3.741 ms  3.709 ms
 9  * * *
10  * * *
11  * * *
12  * * *
13  * * *
14  * * *
15  * * *
16  * * *
17  * * *
18  * * *
19  * * *
20  * * *
21  * * *
22  * * *
23  * * *
24  * * *
25  * * *
26  * * *
27  * * *
28  * * *
29  * * *
30  * * *
"""
        self.assertEqual(TraceResult(ips=[
            '172.31.1.1',
            '49.12.142.82',
            '*',
            '78.47.3.237',
            '85.10.248.221',
            '213.239.208.221',
            '213.239.224.238',
            '104.44.37.193'] + ["*"]*(30-9+1)), parse_traceroute(s))


    def testTracerouteTimedOutTruncated(self):
        # bird-lg-go specific - set latency to None in this case
        s = """
traceroute to azure.microsoft.com (13.107.42.16), 30 hops max, 60 byte packets
 1  172.31.1.1 (172.31.1.1)  6.362 ms
 2  17476.your-cloud.host (49.12.142.82)  0.331 ms
 4  static.237.3.47.78.clients.your-server.de (78.47.3.237)  1.309 ms
 5  static.85.10.248.217.clients.your-server.de (85.10.248.217)  0.940 ms
 6  core11.nbg1.hetzner.com (85.10.250.209)  2.706 ms
 7  core1.fra.hetzner.com (213.239.245.254)  3.809 ms
 8  hetzner.fra-96cbe-1a.ntwk.msn.net (104.44.197.103)  8.055 ms

23 hops not responding.

"""
        self.assertEqual(TraceResult(ips=[
            '172.31.1.1',
            '49.12.142.82',
            '78.47.3.237',
            '85.10.248.217',
            '85.10.250.209',
            '213.239.245.254',
            '104.44.197.103'], notes=["23 hops not responding."]), parse_traceroute(s))

    def testTracerouteNoDNS(self):
        s = """
traceroute to irc.hackint.dn42 (172.20.66.67), 30 hops max, 60 byte packets
 1  172.20.229.114  15.386 ms  15.408 ms  15.409 ms
 2  172.20.229.113  59.462 ms  59.485 ms  59.480 ms
 3  172.20.229.123  80.929 ms * *
 4  * * *
 5  * * 172.20.129.187  152.446 ms
 6  172.20.129.169  165.155 ms  165.375 ms  165.610 ms
 7  172.23.96.1  165.631 ms  182.696 ms  182.695 ms
 8  172.20.66.67  182.695 ms  167.117 ms  187.094 ms"""

        self.assertEqual(TraceResult(ips=[
            '172.20.229.114',
            '172.20.229.113',
            '172.20.229.123',
            '*',
            '*',
            '172.20.129.169',
            '172.23.96.1',
            '172.20.66.67'], latency="182.695 ms"), parse_traceroute(s))

    def testTracerouteNoDNSv6(self):
        s = """traceroute to map.dn42 (fd42:4242:2189:e9::1), 30 hops max, 80 byte packets
 1  fd86:bad:11b7:34::1  33.947 ms  33.932 ms  33.916 ms
 2  fd86:bad:11b7:22::1  43.463 ms  43.467 ms  43.463 ms
 3  fd42:4242:2189:ef::1  45.676 ms  45.665 ms  50.619 ms
 4  fd42:4242:2189:e9::1  208.400 ms  208.398 ms  208.543 ms
"""

        self.assertEqual(TraceResult(ips=[
            'fd86:bad:11b7:34::1',
            'fd86:bad:11b7:22::1',
            'fd42:4242:2189:ef::1',
            'fd42:4242:2189:e9::1'], latency="208.400 ms"), parse_traceroute(s))

    def testTracerouteError(self):
        s = """traceroute to 192.168.123.123 (192.168.123.123), 30 hops max, 60 byte packets
 1  192.168.123.1 (192.168.123.1)  3079.329 ms !H  3079.304 ms !H  3079.299 ms !H
"""

        self.assertEqual(TraceResult(ips=[
            '192.168.123.1'], latency="3079.329 ms !H"), parse_traceroute(s))

if __name__ == '__main__':
    unittest.main()
