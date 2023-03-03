import scrapy,re
from scrapy.exceptions import CloseSpider
import random,time
from scrapy import signals

class SbookSpider(scrapy.Spider):
    name = 'sbook'
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SbookSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider
    
    def start_requests(self):
        url='http://2302--2700.0227.world.chickengotogo.com:1223/o/'
        yield scrapy.Request(url,callback=self.getBase)

    def getBase(self,response):
        
        self.baseurl=response.xpath('/html/body/div[2]/article/div[1]/a[1]/@href').get()
        print(f'获取baseurl：{self.baseurl}')
        yield scrapy.Request(self.baseurl,callback=self.login,dont_filter=True)

    def login(self, response):
        if not re.findall('xyi8269722',response.text):
            print('未登录')
            form_data={
                'username':'912190299@qq.com',
                'password':'rickjick565899'
            }
            print('请求登录')
            yield scrapy.FormRequest.from_response(response,formdata=form_data,callback=self.after_login)
        else:
            print('已登录')
            self.cheader=response.headers
            yield scrapy.Request(self.baseurl,callback=self.parseMainPage,headers=response.headers,dont_filter=True)
    
    def after_login(self,response):
        cookie=response.headers.getlist("set-cookie")
        print(cookie)
        cookie=b' '.join(cookie).decode()
        self.cheader={
            'cookie':cookie
        }
        print('返回主页')
        yield scrapy.Request(self.baseurl,callback=self.parseMainPage,headers=self.cheader,dont_filter=True)
    
    def parseMainPage(self,response):
        if not re.findall('xyi8269722',response.text):
            raise CloseSpider('登录失败')
        print('获取当前银币')
        href=response.xpath('//*[@id="extcreditmenu"]/@href').get()
        yield response.follow(href,callback=self.parseCoin,dont_filter=True)
        print('请求record页')
        recordUrl=self.baseurl+'home.php?mod=space&uid=2059673&do=doing&view=me&from=space'
        yield scrapy.Request(recordUrl,headers=self.cheader,callback=self.postRecordForm,dont_filter=True)
        print('开始回复')
        block=response.xpath(r'//*[@id="category_grid"]/table/tr/td[1]/div/ul/li//@href').getall()
        targets=block[-3:]
        for i in range(len(targets)):
            # print(targets[i])
            meta={
                'delay_request_by':i*62,
                'id':f'回复#{i}'
            }
            yield response.follow(targets[i],callback=self.postForumResponse,meta=meta)

    def parseCoin(self,response):
        self.coinurl=response.url
        self.coinheader=response.headers
        self.initalCoin=response.xpath('//*[@id="ct"]/div[1]/div/ul[2]/li[1]/text()').get()
        print('银币:',self.initalCoin)
        return

    def postForumResponse(self,response):
        formData={
            'message':'看了LZ的帖子，我只想说一句很好很强大！'
        }
        print(f'Post回复#{response.url}')
        formxpath='//*[@id="fastpostform"]'
        yield scrapy.FormRequest.from_response(response,formdata=formData,formxpath=formxpath,meta={'dont_redirect': True})


    def postRecordForm(self,response):
        for i in range(5):
            recordForm={
                'message': 'aaa{}aaa{}aaaaaa'.format(i+random.randint(1,100),random.randint(1,100)),
            }
            meta={
                'delay_request_by':i*62,
                'id':f'记录#{i}',
                'dont_redirect': True,
            }
            print(f'Post表单#{i}')
            yield scrapy.FormRequest.from_response(response,formdata=recordForm,headers=self.cheader,meta=meta)

    def parse(self, response, **kwargs):
        print(f'空parse:{response.url}')
        return
    
    def spider_idle(self, spider):
        print('Last Mission')
        req = scrapy.Request(self.coinurl, callback=self.parseCoin,headers=self.coinheader)
        self.crawler.engine.crawl(req, spider)
