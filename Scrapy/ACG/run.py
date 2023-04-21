import time
import os
from datetime import datetime
def Daily_sbook():
    while True:
        print('%s 开始搜书任务'% datetime.now().strftime('%Y-%m-%d, %H:%M:%S'))
        to_day = datetime.now()
        pth=os.path.split(os.path.realpath(__file__))[0]
        os.chdir(pth)
        log_file = '.\\log\\scrapy_{}_{}_{}.log'.format(to_day.year, to_day.month, to_day.day)
        isExists=os.path.exists(log_file)
        if not isExists:
            fn=open(log_file,'w')
            fn.close()
        os.system("scrapy crawl sbook ")#lcp是我们爬虫的代码名字哦
        print('%s 进入等待'% datetime.now().strftime('%Y-%m-%d, %H:%M:%S'))
        time.sleep(86400)
Daily_sbook()
