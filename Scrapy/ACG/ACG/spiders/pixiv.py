import scrapy
import json,re
from items import IllustInfos,AuthorInfos

class PixivSpider(scrapy.Spider):
    name = 'pixiv'
    allowed_domains = ['pixiv.net']
    start_urls = ['http://pixiv.net/']
    count=0
    def start_requests(self):
        mode=getattr(self,'mode')#search, workid
        if mode=='search':  
            tags=getattr(self,'tags')
            tp=getattr(self,'type','illust_and_ugoira')#illust_and_ugoira, manga
            version=self.settings.get('VERSION')
            word=tags.replace(',',' ')
            print(word)
            tp_dir='illustrations' if tp=='illust_and_ugoira' else 'manga'
            url=f'https://www.pixiv.net/ajax/search/{tp_dir}/{word}?word={word}&order=date_d&mode=all&p=1&s_mode=s_tag_full&type={tp}&lang=zh&version={version}'
            yield scrapy.Request(url,callback=self.parseSearchPage)
        elif mode=='workid':
            artwork_id=getattr(self,'artwork_id')
            url=f'https://www.pixiv.net/artworks/{artwork_id}/'
            yield scrapy.Request(url,callback=self.parseWorkPage)

    def parseSearchPage(self, response):
        infos=json.loads(response.text)
        infos=infos['body']
        # print(infos)
        totalNumber=infos['illust']['total']
        print(totalNumber)
        lenPerPage=len(infos['illust']['data'])
        print(lenPerPage)
        numberofPages=totalNumber//lenPerPage
        for i in range(1,numberofPages+1):
            pagestr=f'p={i}'
            url=response.url.replace('p=1',pagestr)
            yield scrapy.Request(url,callback=self.parseOnePage)

    def parseOnePage(self,response):
        infos=json.loads(response.text)['body']
        dataList=infos['illust']['data']
        for data in dataList:
            artwork_id=data['id']
            url=f'https://www.pixiv.net/artworks/{artwork_id}/'
            yield scrapy.Request(url,callback=self.parseWorkPage)
    
    def parseWorkPage(self, response):
        infos=response.css('meta#meta-preload-data').getall()[0]
        ptt=re.compile("content=\'(\{.*\})")
        infos=re.findall(ptt,infos)[0]
        infos=json.loads(infos)
        illust_info=infos['illust']
        illust_id=list(illust_info.keys())[0]
        illust_info=illust_info[illust_id]#提取到作品信息json
        illustId=illust_info['illustId']
        illustTitle=illust_info['illustTitle']
        illustDescription=illust_info['description']
        illustUploadDate=illust_info['uploadDate']
        illustTags=[tag['tag'] for tag in illust_info['tags']['tags']]
        illustLikeCount=illust_info['likeCount']
        illustBookmarkCount=illust_info['bookmarkCount']
        illustViewCount=illust_info['viewCount']
        illustCommentCount=illust_info['commentCount']
        illustRet=IllustInfos(illustId=illustId,
                            illustTitle=illustTitle,
                            illustDescription=illustDescription,
                            illustUploadDate=illustUploadDate,
                            illustTags=illustTags,
                            illustLikeCount=illustLikeCount,
                            illustBookmarkCount=illustBookmarkCount,
                            illustViewCount=illustViewCount,
                            illustCommentCount=illustCommentCount)
        print(self.count)
        self.count+=1
        user_info=infos['user']
        user_id=list(user_info.keys())[0]
        user_info=user_info[user_id]#提取到作者信息json
        userId=user_info['userId']
        userName=user_info['name']
        userImage=user_info['image']
        userRet=AuthorInfos(authorId=userId,
                            authorName=userName,
                            authorImg=userImage)