import scrapy
from  scrapy import Field
class IllustInfos(scrapy.Item):
    "illustId, illustTitle, illustDescription, illustUploadDate, illustTags, illustLikeCount, illustBookmarkCount, illustViewCount, illustCommentCount,"
    illustId=Field()
    illustTitle=Field()
    illustDescription=Field()
    illustUploadDate=Field()
    illustTags=Field()
    illustLikeCount=Field()
    illustBookmarkCount=Field()
    illustViewCount=Field()
    illustCommentCount=Field()

class AuthorInfos(scrapy.Item):
    "authorId, authorName, authorImg, authorLocation, authorContact, authorAbstract,"
    authorId=Field()
    authorName=Field()
    authorImg=Field()
    authorLocation=Field()
    authorContact=Field()
    authorAbstract=Field()

class TimeChartItem(scrapy.Item):
    title=Field()
    img=Field()
    status=Field()
    weekday=Field()
    weekdayidx=Field()


class AnimaInfos(scrapy.Item):
    '''
    title=Field()
    img=Field()
    tp=Field()
    year=Field()
    region=Field()
    status=Field()
    lastDate=Field()
    VAs=Field()
    directors=Field()
    '''
    title=Field()
    img=Field()
    tp=Field()
    year=Field()
    region=Field()
    status=Field()
    lastdate=Field()
    vas=Field()
    directors=Field()

class Source(scrapy.Item):
    title=Field()
    lineindex=Field()
    domain=Field()
    label=Field()
    href=Field()
    resolution=Field()

