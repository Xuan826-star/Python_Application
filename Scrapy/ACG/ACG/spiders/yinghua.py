import scrapy,re
from items import AnimaInfos,TimeChartItem,Source
from urllib.parse import urlparse
# weekday_name = ["星期一", "星期二", "星期三", 
# "星期四", "星期五", "星期六", "星期日"]
weekday_name = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
class YinghuaSpider(scrapy.Spider):
    name = 'yinghua'
    # allowed_domains = ['yhdm6.top']
    # start_urls = ['https://yhdm6.top/']

    custom_settings={
        'ITEM_PIPELINES':{
        'ACG.pipelines.YinghuaPipeline': 300,
        'ACG.pipelines.MySQLPipeline': 400,
        
        }
    }
    def start_requests(self):
        url='https://yhdm6.top/'
        yield scrapy.Request(url,callback=self.parseHome)
    def parseHome(self, response):
        popularItems=response.xpath('//*[@id="banstem"]/div[2]/div/div[1]/ul/li').getall()
        timeChart=response.xpath('/html/body/div[3]/div[2]/div/div[2]/div/ul')
        for idx in range(len(timeChart)):
            weekday=weekday_name[idx]
            oneDay=timeChart[idx]
            artworksInfo=oneDay.xpath('./li/a')
            for artworkInfo in artworksInfo:
                href=artworkInfo.attrib['href']
                title=artworkInfo.attrib['title']
                img=artworkInfo.attrib['data-original']
                # tp=artworkInfo.css('em.voddate_type::text').get()
                # year=artworkInfo.css('em.voddate_year::text').get()
                # latest=artworkInfo.css('span.pic_text::text').re('(\d+|OVA\d*)')[0]
                status=artworkInfo.css('span.pic_text::text').get()
                Itm=TimeChartItem(title=title,img=img,status=status,weekday=weekday,weekdayidx=idx)
                print('输出时间表item')
                yield Itm
                yield response.follow(href,callback=self.parseSingleInfo)
        


    def parseSearch(self,response):
        pass

    def parseSingleInfo(self,response):
        Info=response.xpath('/html/body/div[2]/div[2]/div/div/div[1]/a')
        title=Info.attrib['title']
        img=Info.attrib['data-original']
        contentDetail=response.xpath('/html/body/div[2]/div[2]/div/div/div[3]/ul/li')
        tempList=contentDetail[0].xpath('./a//text()').getall()
        year=tempList[0]
        region=tempList[1]
        tp=tempList[2:]
        status=contentDetail[1].xpath('./span[@class]//text()').get()
        lastDate=contentDetail[1].xpath('./em//text()').get()
        VAs=contentDetail[2].xpath('./a//text()').getall()
        directors=contentDetail[3].xpath('./a//text()').getall()
        Itm=AnimaInfos(title=title,img=img,tp=tp,year=year,region=region,
                        status=status,lastdate=lastDate,vas=VAs,directors=directors)
        print(f'输出详细信息:{title}')
        yield Itm

        sources=response.css('ul[class="content_playlist clearfix"]')
        for idx in range(len(sources)):
            labels=sources[idx].xpath('.//a/text()').getall()
            hrefs=sources[idx].xpath('.//a/@href').getall()
            # d=dict(zip(labels,hrefs))
            
            for i in range(len(hrefs)):
                ptt_findNumber=re.compile('(\d+)')
                number=re.findall(ptt_findNumber,labels[i])[0]
                if number:
                    number=int(number)
                    new_label=f'第{number}集'
                    labels[i]=new_label
                meta={
                    'title':title,
                    'lineIndex':idx,
                    'label':labels[i]
                }
                print(f'请求视频页:{title}#{labels[i]}')
                yield response.follow(hrefs[i],callback=self.parseVideoSource,meta=meta)

    def parseVideoSource(self,response):
        '//*[@id="play_page"]/div[2]/div/div[1]/div[1]/div[1]/script[1]/text()'
        script=response.xpath('//*[@id="play_page"]/div[2]/div/div[1]/div[1]/div[1]/script[1]/text()').re('"url":"(.*?)"')[0]
        f_url=script.replace('\\','')
        print('请求m3u8文件地址信息:{}'.format(response.meta))
        yield response.follow(f_url,callback=self.parseM3U8,meta=response.meta)
        

    def parseM3U8(self,response):
        href_m3u8=response.text.strip().split('\n')[-1]
        config=response.text.strip().split('\n')[-2]
        ptt=re.compile('RESOLUTION=(\d+x\d+)')
        resolution=re.findall(ptt,config)
        resolution=resolution[0] if len(resolution) else None
        url_obj=urlparse(response.url)
        domain=url_obj.netloc
        pth=url_obj.path
        #某些源(cdn...)是相对href，特殊处理
        if href_m3u8[0]!='/':
            pth=pth.replace('index.m3u8','')
            href_m3u8=pth+href_m3u8
        meta=response.meta
        Itm=Source(title=meta['title'],lineindex=meta['lineIndex'],domain=domain,
                    label=meta['label'],href=href_m3u8,resolution=resolution)
        print(f'输出视频源信息:{meta}')
        yield Itm
        
