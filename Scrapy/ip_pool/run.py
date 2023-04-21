from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import threading,time
from database import *

def crawlIP():
    settings = get_project_settings()

    crawler = CrawlerProcess(settings)
    crawler.crawl('66ip')
    crawler.crawl('ip3366')
    crawler.crawl('kuaidaili')
    crawler.start()

def updateIP():
    start=time.perf_counter()
    server=MySQL(host='127.0.0.1',port=3306,user='root',password='Lucky@2019yx',database='ip_pool')
    Validation=IpTableValidation(server)
    Validation.verifyValid('ip')
    end=time.perf_counter()
    period=end-start
    print(f'updateIP excute time {period}')


# t1=threading.Thread(target=crawlIP)
# t2=threading.Thread(target=updateIP)
# t1.start()
# t2.start()
# crawlIP()
updateIP()