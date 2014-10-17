#!/usr/bin/env python
import zmq
import time
import random
import collections
import sys
import cPickle as pkl
#from pybloomfilter import BloomFilter
import shutil
import multiprocessing
import pickle
import json
import os.path, time
import os


def worker():
	num_queries= int(sys.argv[1])
	start= time.time()
	ts_ext=time.time()
	f= open("resolver_traffic_sample.txt", "w+")
	ctx = zmq.Context()
	s = ctx.socket(zmq.SUB)
	print "Connecting to Umbrella..."
	s.connect('tcp://sgraph.umbrella.com:2201')
	s.setsockopt(zmq.SUBSCRIBE, '')

	count=0
	while count < num_queries:
		a = s.recv()

		
		dns_json=dict(json.loads(a))
		# print "add", dns_json
		# dns_json["name"] = dns_json["name"][:-1]
		# asn = dns_json["asn"]
		server_ip= dns_json["server_ip"]
		print server_ip


		name = dns_json["name"]
		# print name
		f.write(name+","+server_ip+"\n")
		count +=1
	f.close()
	s.close()

worker()



	# #Grab 5 min. worth of data (is data sorted? seems like it for most part, proxy logs are mostly sorted)
	# # while ((time.time()-start) <= 300):
	# print "Buffering logs..."


 #    for line in sys.stdin:
	# 	dns_json=dict(json.loads(a))
	# 	if start ts=="":
	# 		start_ts= dns_json["ts"]
	# 	else:
	# 		curr_ts= dns_json["ts"]

	#     if (curr_ts - start_ts) > 300000.0:




	# # os.rename("stream_logs/output"+str(ts)+".txt", "tmp_stream/output"+str(ts)+".txt")
	# print "count", count	


# d = multiprocessing.Process(name='worker', target=worker())
# d.daemon = True
# d.start()
# d.join()