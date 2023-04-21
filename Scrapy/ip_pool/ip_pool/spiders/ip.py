import scrapy
from scrapy.http import Response
import time
from datetime import datetime

class IpSpider(scrapy.Spider):
    name = 'ip'
    # allowed_domains = ['example.com']
    start_urls = [
        'http://www.66ip.cn/',
        'http://www.ip3366.net/',
        'https://www.kuaidaili.com/free/inha/'
    ]

    def start_requests(self):
        self.headers={
        "USER_AGENT":self.settings.get('USER_AGENT')
        }
        callbacks=[
            self.parse_66ip,
            self.parse_ip3366,
            self.parse_kuaidaili
        ]
        for i in range(len(self.start_urls)):
            yield scrapy.Request(self.start_urls[i],callback=callbacks[i],headers=self.headers)


    def parse_66ip(self, response):
        tb=response.xpath('//*[@id="main"]/div[1]/div[2]/div[1]/table/tr')[1:]
        for tr in tb.getall():
            tr=tr.replace('<tr><td>','')
            tr=tr.replace(' 验证</td></tr>','')
            tr=tr.split('</td><td>')
            ptt='%Y年%m月%d日%H时'
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
            yield response.follow(href,callback=self.parse_66ip)
    
    def parse_ip3366(self, response):
        tb=response.xpath('//*[@id="list"]/table/tbody/tr')
        for tr in tb.getall():
            tr=tr.replace('\r\n                ','')
            tr=tr.replace('<tr><td>','')
            tr=tr.replace('</td>\r\n            </tr>','')
            tr=tr.split('</td><td>')
            ptt='%Y/%m/%d %H:%M:%S'
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
            yield response.follow(href,callback=self.parse_ip3366)
    
    def parse_kuaidaili(self, response):
        tb=response.xpath('//*[@id="list"]/table/tbody/tr')
        ip=tb.css('td[data-title="IP"]::text').getall()
        port=tb.css('td[data-title="PORT"]::text').getall()
        sec=tb.css('td[data-title="匿名度"]::text').getall()
        pro=tb.css('td[data-title="类型"]::text').getall()
        addr=tb.css('td[data-title="位置"]::text').getall()
        delay=tb.css('td[data-title="响应速度"]::text').getall()
        date=tb.css('td[data-title="最后验证时间"]::text').getall()
        ptt='%Y-%m-%d %H:%M:%S'
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
            yield response.follow(href,callback=self.parse_kuaidaili)

