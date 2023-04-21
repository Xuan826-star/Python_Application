import scrapy
import time
from database import MySQL

class KuaidailiSpider(scrapy.Spider):
    name = 'kuaidaili'
    allowed_domains = ['kuaidaili.com']
    start_urls = ['https://www.kuaidaili.com/free/inha/']


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider=super().from_crawler(crawler, *args, **kwargs)
        host=crawler.settings.get('MYSQL_HOST')
        # host=host[0]
        database=crawler.settings.get('MYSQL_DATABASE')
        # database=database[0]
        user=crawler.settings.get('MYSQL_USER')
        # user=user[0]
        password=crawler.settings.get('MYSQL_PASSWORD')
        # password=password[0]
        port=crawler.settings.get('MYSQL_PORT')
        # port=port[0]
        table=crawler.settings.get('MYSQL_TABLE')
        # table=table[0]
        max_ip=crawler.settings.get('MAX_IP')
        mysql=MySQL(host,port,user,password,database)
        spider.table=table
        spider.max_ip=max_ip
        spider.mysql=mysql
        return spider
    
    def parse(self, response):
        tb=response.xpath('//*[@id="list"]/table/tbody/tr')
        ip=tb.css('td[data-title="IP"]::text').getall()
        port=tb.css('td[data-title="PORT"]::text').getall()
        # sec=tb.css('td[data-title="匿名度"]::text').getall()
        # pro=tb.css('td[data-title="类型"]::text').getall()
        # addr=tb.css('td[data-title="位置"]::text').getall()
        # delay=tb.css('td[data-title="响应速度"]::text').getall()
        # date=tb.css('td[data-title="最后验证时间"]::text').getall()
        # ptt='%Y-%m-%d %H:%M:%S'
        for i in range(len(ip)):
            ret={
                'ip':ip[i],
                'port':port[i],
                # 'security':1 if '高匿' in sec[i] else 0,
                # 'protocol':pro[i],
                # 'address':addr[i],
                # 'delay':delay[i].replace('秒',''),
                # 'date':datetime.strptime(date[i],ptt)
            }
            yield ret

        cur=response.css('a[class="active"]')
        nex=cur.xpath('../following-sibling::li[1]/a')
        if nex.get() !=None:
            href=nex.attrib['href']
            time.sleep(1)
            yield response.follow(href,callback=self.parse)