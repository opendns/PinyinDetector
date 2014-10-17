import ngram
import operator
import collections
import cPickle as pkl
import numpy
import tldextract
import langid
import pygeoip
import sys
import math
import operator

class PinyinDetector():

	def __init__(self, infile):
		self.domain_ip_d = collections.defaultdict(str)
		self.infile= infile
		self.gi = pygeoip.GeoIP('GeoIP.dat')
		self.chinese_punycode_doms= set()
		self.score_threshold=0.5
		self.domain_dict= collections.defaultdict(list)
		self.whitelist= self.create_whitelist()
		self.unigram_corpus= collections.Counter()
		self.bigram_corpus= collections.Counter()
		self.trigram_corpus= collections.Counter()
		self.quadgram_corpus= collections.Counter()
		self.cor_uni_sum=0
		self.cor_bi_sum=0
		self.cor_tri_sum=0
		self.cor_quad_sum=0

	"""Read in whitelist"""
	def create_whitelist(self):
		whitelist= set()
		for domain in open("whitelist.txt", "r"):
			domain = domain.strip()
			whitelist.add(domain)
		return whitelist
	
	"""Check if domain has whitelisted words"""
	def whitelisted(self, domain):
		whitelisted= False
		for word in self.whitelist:
			if word in domain:
				whitelisted= True
		return whitelisted

	"""Basic cleaning of domain"""
	def clean(self, domain):

		domain = ''.join([i for i in domain if not i.isdigit()])
		domain = domain.replace(".","")
		domain = domain.replace("-", "")
		return domain


	"""Load pickled Pinyin word corpus from pin_corp.txt"""
	def read_pick_corpus(self):
		uni, bi, tri, quad = pkl.load( open ("PinyinDictionaryCorpus.p", "rb") )
		u, b, t, q = pkl.load( open ("PinyinDomainCorpus.p", "rb") )
		# u_phon, b_phon, t_phon, q_phon = pkl.load( open ("PinyinPhoneticsCorpus.p", "rb") )
		uni +=u #+ u_phon
		bi+=b #+ b_phon
		tri+=t #+ #t_phon
		quad += q #+ q_phon
		return uni, bi, tri, quad

	def getNGrams(self, domain):

		uni_index= ngram.NGram(N=1)
		bi_index = ngram.NGram(N=2)
		tri_index = ngram.NGram(N=3)
		quad_index= ngram.NGram(N=4)

		unigrams= list(uni_index.ngrams(domain))
		bigrams= list(bi_index.ngrams(domain))
		trigrams= list(tri_index.ngrams(domain))
		quadgrams= list(quad_index.ngrams(domain))

		return unigrams, bigrams, trigrams, quadgrams

	def filter_language(self, domain):

		filter_lang_set= set(["en", "es"])

		if langid.classify(domain)[0] in filter_lang_set:
			return True
		return False


	"""Read in live data, clean numbers and dashes, option to filter on SLD, and subdomains"""
	def read_clean_data(self):

		unigram_set= collections.Counter()
		bigram_set= collections.Counter()
		trigram_set= collections.Counter()
		quadgram_set= collections.Counter()

		for line in open(self.infile, "rU"):
			
			line=line.strip()
			domain, ip= line.split(",")
			self.domain_ip_d[domain]=ip

			if self.filter_language(domain)==True:
				continue

			FQDN= domain

			ext=""
			try:
				ext = tldextract.extract(domain)
			except:
				ext=""
		
			if self.whitelisted(domain)==True:
				continue

			#most Pinyin domains have these TLDs, wouldn't have .eu or .ru
			whiteTLDs= set(["com", "cn", "tw", "hk", "net", "info", "biz", "cc", "so", "com.cn", "org.cn", "org", "in", "com.tw","net.cn"])
			

			if ext.suffix not in whiteTLDs:
				continue

			domain= '.'.join(ext[:2])
			domain = self.clean(domain)

			unigrams, bigrams, trigrams, quadgrams= self.getNGrams(domain)

			unigram_c= collections.Counter(unigrams)
			bigram_c= collections.Counter(bigrams)
			trigram_c= collections.Counter(trigrams)
			quadgram_c= collections.Counter(quadgrams)

			self.domain_dict[FQDN].append(unigram_c)
			self.domain_dict[FQDN].append(bigram_c)
			self.domain_dict[FQDN].append(trigram_c)
			self.domain_dict[FQDN].append(quadgram_c)


	"""Create sum of all corpus totals"""
	def sum_cor(self, c):
		c= dict(c)
		total=0
		for k, v in c.items():
			total+=v
		return total

	"""Calculate bigram probability"""
	def get_bigram_probability(self, bigram):
		return float(self.bigram_corpus[bigram]) / float(self.uni_corpus[bigram[0:1]])

	"""Calculate trigram probability"""
	def get_tri_probability(self, trigram):
		return float(self.trigram_corpus[trigram])/float(self.bigram_corpus[trigram[0:2]])

	"""Calculate quadgram probability"""
	def get_quad_probability(self, quadgram):
		return float(self.quadgram_corpus[quadgram])/float(self.trigram_corpus[quadgram[0:3]])

# """Smoothing function to handle zero division error"""
# 	def get_smooth_probability(self, bigram_corpus, bigram, unigram_corpus):
# 		return float(bigram_corpus[bigram])/float(uni_corpus[bigram[0]]) * 0.9 + float(uni_corpus[bigram[0]])/cor_uni_sum *0.05 +float(uni_corpus[bigram[1]])/cor_uni_sum *0.05

	def create_probability_vectors(self):

		bigram_result={}
		trigram_result={}
		quadgram_result={}

		total_d= collections.defaultdict(float)

		for domain, grams in self.domain_dict.items():

			bi_val=1.0
			tri_val=1.0
			quad_val=1.0

			bi= dict(grams[1])
			tri= dict(grams[2])
			quad= dict(grams[3])


			bigram_probability= 0.0
			trigram_probability= 0.0
			quadgram_probability= 0.0

			for bigram, freq in bi.items():

				try:
					bigram_probability= self.get_bigram_probability(bigram)
				except:
					continue

				if bigram_probability == 0.0:
					bigram_probability= 1.0/self.cor_bi_sum

				bigram_probability = bigram_probability**freq

			for trigram, freq in tri.items():
				try:
					trigram_probability= self.get_tri_probability(trigram)
				except:
					continue

				if trigram_probability == 0.0:
					trigram_probability= 1.0/self.cor_tri_sum
				trigram_probability = trigram_probability**freq

			for quadgram, freq in quad.items():
				try:
					quadgram_probability= self.get_quad_probability(quadgram)
				except:
					continue

				if quadgram_probability == 0.0:
					quadgram_probability= 1.0/self.cor_quad_sum

				quadgram_probability = quadgram_probability**freq

			bi_val*= bigram_probability
			tri_val*= trigram_probability
			quad_val*= quadgram_probability

			total_domain_score= ((1.0*float(bi_val)) + (2.0*float(tri_val)) + (3.0*float(quad_val))) /6.0
			total_d[domain]=total_domain_score
		return dict(total_d)

	def getCC(self, ip):
		country_code=""
		try:
			country_code= self.gi.country_code_by_addr(ip)
		except:
			country_code=""
		return country_code

	def getCC_weight(self, cc):
		cc_weight=0.0
		if cc == 'CN' or cc=='HK' or cc=='TW':
			cc_weight = 0.5
		return cc_weight

	def get_lang_weight(self, domain):		
		lang_weight = 0.0
		if langid.classify(domain)[0] == "zh":
			lang_weight = 0.5
		return lang_weight

	def get_punycode_weight(self, domain):
		punycode_weight= 0.0
		if "xn--" in domain:
			punycode_weight=0.5
		return punycode_weight

	"""Words unique to Pinyin only (confirmed by native speakers)"""
	def check_giveaway_words(self, domain):
		g_score= 0.0
		giveaways= set(["zhan", "zhuo", "zhen", "zhuan", "zhon", "chang", "chuan", "cheng", "xiang", "qian", "xiong", "xian", "xuan", "jiang", "chuang", "ijin"])
		for g in giveaways:
			if g in domain:
				g_score +=.5
		return g_score


if __name__ == "__main__":
	
	pd= PinyinDetector(sys.argv[1])
	uni_corpus, bi_corpus, tri_corpus, quad_corpus= pd.read_pick_corpus()
	pd.unigram_corpus = uni_corpus
	pd.bigram_corpus = bi_corpus
	pd.trigram_corpus = tri_corpus
	pd.quad_corpus = quad_corpus
	pd.read_clean_data()
	pd.cor_uni_sum= pd.sum_cor(uni_corpus)
	pd.cor_bi_sum= pd.sum_cor(bi_corpus)
	pd.cor_tri_sum= pd.sum_cor(tri_corpus)
	pd.cor_quad_sum= pd.sum_cor(quad_corpus)

	total_d= pd.create_probability_vectors()
	scoring_vector=[]
	total_probability=0.0
	unfiltered_scoring_vector=[]
	# for domain, prob in total_d.items():

	# 	total_domain_score=0
	# 	ip = pd.domain_ip_d[domain]
	# 	cc = pd.getCC(ip)
	# 	cc_weight= pd.getCC_weight(cc)
	# 	lang_weight= pd.get_lang_weight(domain)
	# 	punycode_weight= pd.get_punycode_weight(domain)
	# 	total_domain_score= prob+ lang_weight + cc_weight + punycode_weight
	# 	scoring_vector.append((domain, total_domain_score))
	# 	total_probability+=total_domain_score

	# scoring_vector= sorted(scoring_vector, key=operator.itemgetter(1), reverse=True)

	# f= open('filtered_domains.txt', 'w+')
	# normalized_score=0
	# count=0
	# print "(Domain, Score)"
	# f.write("Domain, Score"+"\n")
	# for item in scoring_vector:
	# 	domain= item[0]
	# 	score= item[1]
	# 	if score < pd.score_threshold:
	# 		continue
	# 	normalized_score = score/total_probability
	# 	print (domain, normalized_score)
	# 	f.write(str(domain)+", "+str(normalized_score)+"\n")
	# 	count+=1

	for domain, prob in total_d.items():

		total_domain_score=0
		ip = pd.domain_ip_d[domain]
		cc = pd.getCC(ip)
		cc_weight= pd.getCC_weight(cc)
		lang_weight= pd.get_lang_weight(domain)
		punycode_weight= pd.get_punycode_weight(domain)
		giveaway_weight= pd.check_giveaway_words(domain)
		total_domain_score= prob+ lang_weight + cc_weight + punycode_weight + giveaway_weight
		scoring_vector.append((domain, total_domain_score))
		unfiltered_scoring_vector.append((domain, prob))
		total_probability+=total_domain_score

	scoring_vector= sorted(scoring_vector, key=operator.itemgetter(1), reverse=True)
	unfiltered_scoring_vector= sorted(unfiltered_scoring_vector, key=operator.itemgetter(1), reverse=True)

	f= open('filtered_domains.txt', 'w+')
	f1 = open("unfiltered_domains.txt", "w+")
	normalized_score=0
	count=0
	print "(Domain, Score)"
	f.write("Domain, Score"+"\n")
	f1.write("Domain, Score"+"\n")
	for item in unfiltered_scoring_vector:
		domain = item[0]
		score= item[1]
		f1.write(str(domain)+", "+str(score)+", ("+ str(langid.classify(domain)[0])+", "+str(langid.classify(domain)[1])+")\n")

	for item in scoring_vector:
		domain= item[0]
		score= item[1]
		if score < pd.score_threshold:
			continue
		normalized_score = score/total_probability
		# print (domain, normalized_score)
		f.write(str(domain)+", "+str(normalized_score)+"\n")
		count+=1


