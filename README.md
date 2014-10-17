PinyinDetector
==============

Summary: Language identification tool to identify Pinyin language in DNS A Records filter out Chinese domains. Use "Bag of words" approach using n-grams (currently using bi, tri, quad grams) and Naive Bayes for language detection. 

Dependencies:

NGrams

PyGeoIP

LangID

TLDExtract

PyZmq

N-Gram Probability Calculations:
--------------------------------

Bigram:
P(a|b) = P(ab) / P(a)

Trigram:
P(ab|c) = P(abc) / P(ab)

Quadgram:
P(abc|d) = P(abcd) / P(abc)

Total:
(P(a|b) + 2*P(ab|c) + 3*P(abc|d)) / 6


Usage: 

Run the detection algorithm with input csv file in domain, ip format (exampele file provided):

python pinyin_detector.py resolver_traffic_sample.txt

New Corpus taken from:
http://en.wikibooks.org/wiki/Category:Pinyin

