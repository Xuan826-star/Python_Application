import pymysql as sql
import aiohttp,time,asyncio,json
from datetime import datetime
from lxml import etree
from concurrent.futures import ThreadPoolExecutor,wait

class MySQL():
    __name__='localInstance'
    def __init__(self,host,port,user,password,database) -> None:
        port=int(port)
        self.connection = sql.connect(host=host,
            user=user,
            port=port,
            password=password,
            database=database)
        self.current_database=database
        self.cursor=self.connection.cursor()
    
    def selectdb(self,name) -> None:
        cmd="USE %s;" %name
        self.cursor.execute(cmd)
        self.current_database=name

    def runcmd(self,cmd) -> list:
        resultlist=[]
        sqllist=cmd.split(';')
        cmds=sqllist[0:-1]
        for cmd in cmds:
            try:
                self.cursor.execute(cmd)
                resultlist.append(self.cursor.fetchall())
                self.connection.commit()
            except:
                self.connection.rollback()
        return resultlist

    def insertdata(self,table,data) -> str:
        cursor=self.connection.cursor()
        try:
            cols = ", ".join('`{}`'.format(k) for k in data.keys())
            val_cols = ', '.join('%({})s'.format(k) for k in data.keys())
            sql = "insert into `"+table+"`(%s) values(%s)"
            res_sql = sql % (cols, val_cols)
            cursor.execute(res_sql, data)  # 将字典data传入
            self.connection.commit()
            return 'Insert'
        except Exception as e:
            print(f'MYSQL Insert ERROR:{e.args}')
            cmd=f'''
            SELECT `COLUMN_NAME`
            FROM `information_schema`.`COLUMNS`
            WHERE (`TABLE_NAME` = '{table}')
            AND (`COLUMN_KEY` = 'PRI');
            '''
            cursor.execute(cmd)
            keytuplelist=self.cursor.fetchall()
            primarykey=[i[0] for i in keytuplelist]
            data_copy=data.copy()
            for key in primarykey:
                data_copy.pop(key)
            updatelist=[]
            for k in data_copy.keys():
                updatelist.append('%s = values(%s)'%(k,k))
            updatestr=','.join(updatelist)
            addition=' on duplicate key update '+updatestr
            res_sql=res_sql+addition
            try:
                cursor.execute(res_sql, data)  # 将字典data传入
                self.connection.commit()
                print('success')
                return 'Update'
            except Exception as e:
                print(f'MYSQL Update ERROR:{e.args}')
                self.connection.rollback()
                return 'Fail'
    
    def checkexists(self,table,keys,data) -> bool:
        isexists=True
        whereClause=[]
        for i in range(len(keys)):
            addition=f"{keys[i]}='{data[i]}'"
            whereClause.append(addition)
        whereClause=' AND '.join(whereClause)
        cmd=f'''
        SELECT *
        FROM {table}
        WHERE {whereClause};
        '''
        self.cursor.execute(cmd)
        res=self.cursor.fetchone()
        if res==None:
            isexists=False
        # print(res)
        return isexists

    # def __del__(self):
    #     self.cursor.close()
    #     self.connection.close()

class IpTableValidation():
    def __init__(self,database: MySQL) -> None:
        self.database=database
        self.http_url='http://www.chinaz.com'
        self.https_url='https://www.baidu.com'
        self.timeout=10
        self.user_agent="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
        self.hidden_url='http://httpbin.org/get'
        self.my_ip='171.34.209.16'
    
    def verifyRow(self,tup,table):
        new_loop =  asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop=asyncio.get_event_loop()
        ip=tup[0]
        port=tup[1]
        score=tup[-1]
        httpRes=self.verifySingle(ip,port,'http')
        httpsRes=self.verifySingle(ip,port,'https')
        addressRes=self.verifyAddress(ip)
        hiddenRes=self.verifyHidden(ip,port)
        httptask=asyncio.ensure_future(httpRes)
        httpstask=asyncio.ensure_future(httpsRes)
        addresstask=asyncio.ensure_future(addressRes)
        hiddentask=asyncio.ensure_future(hiddenRes)
        tasks=[httptask,httpstask,addresstask,hiddentask]
        loop.run_until_complete(asyncio.wait(tasks))
        item={
            'ip':ip,
            'port':port,
            'datetime':datetime.now(),
        }
        for t in tasks:
            item.update(t.result())
        if not (item['http_status'] or item['https_status']):
            score-=1
        else:
            score+=1
        item.update({'score':score})
        self.database.insertdata(table,item)
        
            

    
    def verifyValid(self, table):
        #read the table
        showcmd='''
        SELECT `ip`,`port`,`score` FROM ip;
        '''
        self.database.cursor.execute(showcmd)
        tupleList=self.database.cursor.fetchall()
        with ThreadPoolExecutor(max_workers=10) as pool:
            all_tasks=[pool.submit(self.verifyRow(tup,table)) for tup in tupleList]
            wait(all_tasks)
            print('all finished')
            

    async def verifySingle(self, ip, port, types):
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
    
    async def verifyAddress(self,ip):
        print('Verify address %s'%(ip))
        headers = {"User-Agent": self.user_agent}
        url=f'https://ip.cn/ip/{ip}.html'
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            try:
                async with session.get(url, headers=headers, timeout=self.timeout) as res:
                    html=etree.HTML(await res.text())
                    address=html.xpath('//*[@id="tab0_address"]')[0].text
            except Exception as e:
                print(e)
                address=None
        return{'address':address}
    
    async def verifyHidden(self,ip, port):
        print('Verify hidden %s:%s'%(ip,port))
        headers = {"User-Agent": self.user_agent}
        proxy = 'http://'+ str(ip) + ':' + str(port)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.hidden_url, headers=headers, proxy=proxy, timeout=self.timeout) as resp:
                    response=json.loads(await resp.text(encoding='utf-8'))
            except Exception as e:
                print('Hidden url get fail: ', e,e.args)
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