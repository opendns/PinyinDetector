import sys
import collections


ip_dom_d= collections.defaultdict(list)
ip=""

for line in sys.stdin:
	line = line.strip()

	if line.startswith("------------"):

		line=line.replace("------------", "")
		line=line.strip()
		ip=line

	elif line!="" and not line.startswith("------------"):
		ip_dom_d[ip].append(line)

for ip, domain_list in ip_dom_d.items():
	for domain in domain_list:
		print domain, ip
		# f.write(domain+","+ip + "\n")


		


