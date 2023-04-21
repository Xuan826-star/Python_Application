# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from datetime import datetime
import time,json,geoip2.database,aiohttp,asyncio,nest_asyncio
from lxml import etree
nest_asyncio.apply()


class FilterPipeline:

    def open_spider(self,spider):
        print('Open Spider')
        cmd=f"""
        CREATE TABLE IF NOT EXISTS {spider.table} ( 
            `ip` VARCHAR(15) NOT NULL,
            `port` VARCHAR(10) NOT NULL,
            `http_status` BOOL,
            `http_speed` FLOAT,
            `https_status` BOOL,
            `https_speed` FLOAT,
            `hidden_id` TINYINT,
            `address` TEXT,
            `vpn` BOOL,
            `datetime` DATETIME,
            `score` INT DEFAULT 0,
            PRIMARY KEY (`ip`,`port`)
        ) DEFAULT CHARSET=utf8;
        """
        spider.mysql.runcmd(cmd)
        cmd=f"SELECT count(*) FROM {spider.table} WHERE `score`>=0;"
        spider.mysql.cursor.execute(cmd)
        spider.num_rows=spider.mysql.cursor.fetchone()[0]
        print(f'Open in {spider.num_rows} rows of data.')
        if spider.num_rows>=spider.max_ip:
            spider.crawler.engine.close_spider(spider,'Reach the Max IP')
    
    def process_item(self,item,spider):
        if spider.num_rows>=spider.max_ip:
            spider.crawler.engine.close_spider(spider,'Reach the Max IP')
        keys=list(item.keys())
        data=list(item.values())
        isExists=spider.mysql.checkexists(spider.table,keys,data)
        if isExists:
            print('Exists Drop %s:%s'%(item['ip'],item['port']))
            raise DropItem('Exists')
        return item


class ValidationPipeline:
        
    def __init__(self, user_agent, http_url, https_url, timeout, forigen_url, hidden_url,my_ip):
        self.user_agent=user_agent
        self.http_url=http_url
        self.https_url=https_url
        self.timeout=timeout
        self.forigen_url=forigen_url
        self.hidden_url=hidden_url
        self.my_ip=my_ip
        # self.reader=geoip2.database.Reader('./GeoLite2-City.mmdb')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent=crawler.settings.get('USER_AGENT'),
            http_url=crawler.settings.get('VERIFY_HTTP_URL'),
            https_url=crawler.settings.get('VERIFY_HTTPS_URL'),
            timeout=crawler.settings.get('VERIFY_SPIDER_REQUESTS_TIMEOUT'),
            forigen_url=crawler.settings.get('VERIFY_COUNTRY_URL'),
            hidden_url=crawler.settings.get('VERIFY_HIDDEN_URL'),
            my_ip=crawler.settings.get('MY_IP'),
        )

    async def verifyValid(self, ip, port, types):
        print('Verify %s validity %s:%s'%(types,ip,port))
        headers = {"User-Agent": self.user_agent}
        proxies = {'http': 'http://'+ str(ip) + ':' + str(port), 'https':'https://'+  str(ip) + ':' + str(port)}
        urls = {'http':self.http_url, 'https':self.https_url}
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            try:
                start = time.time()
                async with session.get(urls[types.lower()], headers=headers, proxy=proxies[types], timeout=self.timeout) as res:
                    speed = round(time.time() - start, 2)
            except:
                return {f'{types}_status': False, f'{types}_speed': None}
            else:
                
                return {f'{types}_status': True, f'{types}_speed': speed}

    async def verifyHidden(self,ip, port):
        print('Verify hidden %s:%s'%(ip,port))
        headers = {"User-Agent": self.user_agent}
        proxy = 'http://'+ str(ip) + ':' + str(port)
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            
            try:
                async with session.get(self.hidden_url, headers=headers, proxy=proxy, timeout=self.timeout) as resp:
                    response=json.loads(await resp.text(encoding='utf-8'))
            except Exception as e:
                print('Hidden url get fail: ',e, e.args)
                return {'hidden_id': None}
            else:
                try:
                    origin_ip = response.get('origin', '')
                    proxy_connection = response['headers'].get('Proxy-Connection', None)
                except:
                    proxy_connection = None
                # 透明
                if(',' in origin_ip):
                    origin = origin_ip.split(',')
                    for ip in origin:
                        if(ip == self.my_ip):
                            hidden_id = 1
                            break
                        else:
                            hidden_id = 2
                # 匿名
                elif(proxy_connection):
                    hidden_id = 2
                # 高匿
                else:
                    hidden_id = 3
                
                return {'hidden_id': hidden_id}
    
    async def verifyAddress(self,ip):
        print('Verify address %s'%(ip))
        headers = {"User-Agent": self.user_agent}
        url=f'https://ip.cn/ip/{ip}.html'
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            try:
                async with session.get(url, headers=headers, timeout=self.timeout) as res:

                    html=etree.HTML(await res.text())
                    address=html.xpath('//*[@id="tab0_address"]')[0].text
            except:
                address=None
        return{'address':address}
    
    async def verifyVPN(self,ip, port):
        print('Verify VPN %s:%s'%(ip,port))
        headers = {"User-Agent": self.user_agent}
        proxy = 'http://'+str(ip) + ':' + str(port)
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            try:
                async with session.get(self.forigen_url, headers=headers, proxy=proxy, timeout=self.timeout) as res:
                    pass
            except:
                    
                return {'vpn':False}
            else:
                    
                return {'vpn':True}

    def process_item(self,item,spider):
        a=self.verifyValid(item['ip'],item['port'],'http')
        b=self.verifyValid(item['ip'],item['port'],'https')
        c=self.verifyHidden(item['ip'],item['port'])
        d=self.verifyVPN(item['ip'],item['port'])
        e=self.verifyAddress(item['ip'])
        tasks=[]
        for i in [a,b,c,d,e]:
            task=asyncio.ensure_future(i)
            tasks.append(task)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(tasks))
        for t in tasks:
            item.update(t.result())
        if not (item['http_status'] or item['https_status']):
            print('Drop %s:%s'%(item['ip'],item['port']))
            raise DropItem('Invalid')
        item.update({'datetime':datetime.now()})
        
        return item



class MySQLPipeline:
        
    def process_item(self, item, spider):
        status=spider.mysql.insertdata(self.table,item)
        print('Update database %s:%s'%(item['ip'],item['port']))
        if status=='Insert':
            spider.num_rows+=1
        return item

    def close_spider(self,spider):
        spider.mysql.connection.close()