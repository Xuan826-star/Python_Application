# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import re
import  pymysql as sql
from pymysql.err import IntegrityError
from items import *
class AcgPipeline:
    def process_item(self, item, spider):
        return item

class YinghuaPipeline:
    def process_item(self, item, spider):
        if type(item)==TimeChartItem:
            ptt_findNumber=re.compile('(\d+)')
            number=re.findall(ptt_findNumber,item['status'])[0]
            if number:
                number=int(number)
                new_status=f'更新至第{number}集'
                item['status']=new_status
        
        elif type(item)==AnimaInfos:
            item['year']=int(item['year'])
            NoneList=['内详','未知']
            if len(item['vas'])==0 or item['vas'][0] in NoneList:
                item['vas']=None
            if len(item['directors'])==0 or item['directors'][0] in NoneList:
                item['directors']=None
            
        elif type(item)==Source:
            # if item['resolution']:
            #     item['resolution']=item['resolution'].split('x')
            if not item['label'].isprintable():
                item['label']=''.join(x for x in item['label'] if x.isprintable())
        
        #将list转换成str
        for key in list(item.keys()):
            if type(item[key])==list:
                item[key]=''.join(i for i in item[key])
        return item

class MySQLPipeline:
    def __init__(self, host, database, user, password, port, table):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.table=table
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST'),
            database=crawler.settings.get('MYSQL_DATABASE'),
            user=crawler.settings.get('MYSQL_USER'),
            password=crawler.settings.get('MYSQL_PASSWORD'),
            port=crawler.settings.get('MYSQL_PORT'),
            table=crawler.settings.get('MYSQL_TABLE'),
        )
    
    def executesqls(self,sql):
        resultlist=[]
        sqllist=sql.split(';')
        cmds=sqllist[0:-1]
        for cmd in cmds:
            try:
                self.cursor.execute(cmd)
                resultlist.append(self.cursor.fetchall())
                self.connection.commit()
            except:
                self.connection.rollback()
        return resultlist

    def open_spider(self,spider):
        self.connection = sql.connect(host=self.host,
                    user=self.user,
                    password=self.password,
                    port=self.port,
                    database=self.database)
        self.cursor=self.connection.cursor()
        if spider.name=='yinghua':
            cmd=f"""
            USE {self.database};
            CREATE TABLE IF NOT EXISTS {self.table['TIMECHART']} ( 
                `weekday` VARCHAR(10) NOT NULL,
                `weekdayidx` INT NOT NULL,
                `title` VARCHAR(50) NOT NULL,
                `img` TEXT NOT NULL,
                `status` TEXT NOT NULL,
                PRIMARY KEY (`weekdayidx`,`title`)
            ) DEFAULT CHARSET=utf8;
            CREATE TABLE IF NOT EXISTS {self.table['ANIMAINFO']} ( 
                `title` VARCHAR(50) NOT NULL,
                `img` TEXT,
                `tp` TEXT,
                `year` INT,
                `region` CHAR(10),
                `status` CHAR(10),
                `lastdate` CHAR(5),
                `vas` TEXT,
                `directors` TEXT,
                PRIMARY KEY (`title`)
            ) DEFAULT CHARSET=utf8;
            CREATE TABLE IF NOT EXISTS {self.table['VIDEOSOURCE']} ( 
                `title` VARCHAR(50) NOT NULL,
                `lineindex` INT NOT NULL,
                `domain` TEXT NOT NULL,
                `label` CHAR(10) NOT NULL,
                `href` TEXT NOT NULL,
                `resolution` TEXT,
                PRIMARY KEY (`title`,`lineIndex`,`label`)
            ) DEFAULT CHARSET=utf8;
            """
        self.executesqls(cmd)

        # cmd=f"SELECT count(*) FROM {self.table};"
        # self.cursor.execute(cmd)
        # self.num_rows=self.cursor.fetchone()[0]
        

    def insert_dict(self,table,data,spider):
        try:
            cols = ", ".join('`{}`'.format(k) for k in data.keys())
            val_cols = ', '.join('%({})s'.format(k) for k in data.keys())
            sql = "insert into `"+table+"`(%s) values(%s)"
            res_sql = sql % (cols, val_cols)
            self.cursor.execute(res_sql, data)  # 将字典data传入
            self.connection.commit()
        except Exception as e:
            spider.logger.info(f'ERROR:{e.args}')
            cmd=f'''
            SELECT `COLUMN_NAME`
            FROM `information_schema`.`COLUMNS`
            WHERE (`TABLE_NAME` = '{table}')
            AND (`COLUMN_KEY` = 'PRI');
            '''
            self.cursor.execute(cmd)
            keytuplelist=self.cursor.fetchall()
            primarykey=[i[0] for i in keytuplelist]
            data_copy=data.copy()
            for key in primarykey:
                data_copy.pop(key)
            updatelist=[]
            for k in data_copy.keys():
                updatelist.append('%s = values(%s)'%(k,k))
            updatestr=''.join(updatelist)
            addition=' on duplicate key update '+updatestr
            res_sql=res_sql+addition
            try:
                self.cursor.execute(res_sql, data)  # 将字典data传入
                self.connection.commit()
            except Exception as e:
                print(e)



    def process_item(self,item, spider):
        if type(item)==TimeChartItem:
            table=self.table['TIMECHART']
        elif type(item)==AnimaInfos:
            table=self.table['ANIMAINFO']
        elif type(item)==Source:
            table=self.table['VIDEOSOURCE']
        self.insert_dict(table,dict(item),spider=spider)
        print('Save table %s'%(table))
        return item



    def close_spider(self,spider):
        self.connection.close()