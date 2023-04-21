import scrapy
from database import MySQL

class A66ipSpider(scrapy.Spider):
    name = '66ip'
    allowed_domains = ['66ip.cn']
    start_urls = ['http://www.66ip.cn/']

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
        tb=response.xpath('//*[@id="main"]/div[1]/div[2]/div[1]/table/tr')[1:]
        for tr in tb.getall():
            tr=tr.replace('<tr><td>','')
            tr=tr.replace(' 验证</td></tr>','')
            tr=tr.split('</td><td>')
            # ptt='%Y年%m月%d日%H时'
            ret={
                'ip':tr[0],
                'port':tr[1],
                # 'address':tr[2],
                # 'security':1 if '高匿' in tr[3] else 0,
                # 'date':datetime.strptime(tr[4],ptt)
            }
            yield ret

        cur=response.css('a.pageCurrent')
        nex=cur.xpath('./following-sibling::a[1]')
        if nex.get() !=None:
            href=nex.attrib['href']
            yield response.follow(href,callback=self.parse)
