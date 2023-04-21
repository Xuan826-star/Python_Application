import scrapy
from database import MySQL

class Ip3366Spider(scrapy.Spider):
    name = 'ip3366'
    allowed_domains = ['ip3366.net']
    start_urls = ['http://www.ip3366.net/']

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
        for tr in tb.getall():
            tr=tr.replace('\r\n                ','')
            tr=tr.replace('<tr><td>','')
            tr=tr.replace('</td>\r\n            </tr>','')
            tr=tr.split('</td><td>')
            # ptt='%Y/%m/%d %H:%M:%S'
            ret={
                'ip':tr[0],
                'port':tr[1],
                # 'security':1 if '高匿' in tr[2] else 0,
                # 'protocol':tr[3],
                # # 'support':tr[4],
                # 'address':tr[5],
                # 'delay':tr[6].replace('秒',''),
                # 'date':datetime.strptime(tr[7],ptt)
            }
            yield ret

        cur=response.css('font[color="#FF0000"]')
        nex=cur.xpath('./following-sibling::a[1]')
        if nex.get() !=None:
            href=nex.attrib['href']
            yield response.follow(href,callback=self.parse)
