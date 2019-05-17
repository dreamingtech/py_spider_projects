# coding = utf-8

from scrapy import cmdline
import sys, os


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

cmdline.execute("scrapy crawl jav".split())
