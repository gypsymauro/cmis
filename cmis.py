LOGIN="/service/api/login"

import urllib.request, urllib.parse
import json
import datetime
from xml.dom.minidom import parse
import xml.dom.minidom

import logging
import configparser
import os

class Cmis:
    def __init__(self,site=None):
        self.ticket = None

        self.config = configparser.ConfigParser()

        
        self.config.read(__file__[:-2] + 'ini')

        if site:
            self.site = site
        else:
            self.site = self.config['ALFRESCO']['site']
        
        self.host = self.config['ALFRESCO']['hostname']
        self.port = self.config['ALFRESCO']['port']
        self.username = self.config['ALFRESCO']['username']
        self.password = self.config['ALFRESCO']['password']
            

    def composeURL(self, url):
        composedurl = 'http://%s:%s/alfresco%s' % (self.host, self.port, url)

        logging.debug('composed url: %s' % composedurl)
        return composedurl
    
    def login(self):
        data = {
            'username' : self.username,
            'password' : self.password
        }

        data = json.dumps(data).encode('utf8')
              
        loginurl=self.composeURL(LOGIN)
        
        req  = urllib.request.Request( loginurl, data=data, headers={'content-type': 'application/json'})
        try:
            resp = urllib.request.urlopen(req)
            logging.info('Cmis connected ok')

        except:
            logging.error('Connection error')
            return False
        
        resp=json.loads(resp.read().decode('utf8'))
        self.ticket = resp['data']['ticket']

        logging.debug('Cmis ticket: %s' % self.ticket)
        return True

    def getDocPath(self, filename, data):
        path = data.strftime('%Y/%m/%d/')+filename
        return path        
    

    def getChilds(self,protopath):
        url = '/service/cmis/p/Siti/' + self.site +'/documentLibrary/' + protopath + '/children?alf_ticket=' + self.ticket

        childurl = self.composeURL(url)

        items = []
        i=0
        
        try:
            req = urllib.request.Request( childurl )
       
            resp = urllib.request.urlopen(req)
            resp = resp.read().decode('utf8')
        except urllib.error.HTTPError:
            logging.warning('alfresco objet not found %s' % childurl)
            return items
                  
        dom = xml.dom.minidom.parseString(resp)


        logging.debug(dom.toprettyxml())
        for entry in dom.getElementsByTagName("entry"):
            item = {}
            for title in entry.getElementsByTagName("title"):
                title=title.firstChild.wholeText

            for path in entry.getElementsByTagName("cmisra:pathSegment"):
                path=path.firstChild.wholeText

            for summary in entry.getElementsByTagName("summary"):
                if summary.firstChild:                    
                    summary=summary.firstChild.wholeText
                else:
                    summary=''

            item['title']=title
            item['path']=path          
#            item['quotedpath']=urllib.parse.quote_plus(protopath+'/'+path)
            item['cmispath']=protopath+'/'+path
            item['id']=i
            item['summary']=summary
            i=i+1

            items.append(item)

        return items

  
    def getFile(self,path):
        url = '/service/cmis/p/Siti/' + self.site + '/documentLibrary/' + urllib.parse.quote(path) + '/content?alf_ticket=' + self.ticket

        fileurl = self.composeURL(url)

        req = urllib.request.Request(fileurl)             
        resp = urllib.request.urlopen(req)
        resp = resp.read()
        return resp


    def getContent(self,contenturl):
        #returns the file object giving the content's url
        fileurl = contenturl + '?alf_ticket=' + self.ticket

        logging.info(fileurl)
        
        req = urllib.request.Request(fileurl)             
        resp = urllib.request.urlopen(req)
        resp = resp.read()
        return resp
    
               

    def getVersions(self,filepath):
        url = '/service/cmis/p/Siti/' + self.site + '/documentLibrary/' + urllib.parse.quote(filepath) + '/versions?alf_ticket=' + self.ticket

        fileurl = self.composeURL(url)
        req = urllib.request.Request(fileurl)             
        resp = urllib.request.urlopen(req)

        try:
            req = urllib.request.Request( fileurl )
       
            resp = urllib.request.urlopen(req)
            resp = resp.read().decode('utf8')
        except urllib.error.HTTPError:
            logging.warning('alfresco objet not found %s' % fileurl)
            return items
                  
        dom = xml.dom.minidom.parseString(resp)

        i=0
        items=[]
        
        for entry in dom.getElementsByTagName("entry"):
            item = {}

            for content in entry.getElementsByTagName("content"):
                content = content.getAttribute('src')

            for title in entry.getElementsByTagName("title"):
                title=title.firstChild.wholeText

            for path in entry.getElementsByTagName("cmisra:pathSegment"):
                path=path.firstChild.wholeText

            for summary in entry.getElementsByTagName("summary"):
                if summary.firstChild:
                    summary=summary.firstChild.wholeText
                else:
                    summary=''


                


            for obj in entry.getElementsByTagName("cmis:propertyString"):
                    #there is one, loop if you must.

                propdefid = obj.getAttribute('propertyDefinitionId')

                if propdefid == 'cmis:versionLabel':
                    value = obj.getElementsByTagName('cmis:value')
                    value = value[0]
                    data = value.firstChild.data                    
                    version=data

                if propdefid == 'cmis:checkinComment':
                    value = obj.getElementsByTagName('cmis:value')
                    versionlabel=''
                    if value != []:
                        value = value[0]
                        if value.firstChild:
                            data = value.firstChild.data                    
                            versionlabel=data


            for obj in entry.getElementsByTagName("cmis:propertyId"):
                propdefid = obj.getAttribute('propertyDefinitionId')
                if propdefid == 'cmis:objectId':
                    value = obj.getElementsByTagName('cmis:value')
                    value = value[0]
                    data = value.firstChild.data                    
                    objectid=data

                    

            item['content']=content
                    
            item['title']=title
            item['path']=path
            item['summary']=summary
            item['version']=version
            item['versionlabel']=versionlabel
            item['objectid']=objectid[24:]

            item['cmispath']=filepath+'/'+path
        
            item['id']=i
            i=i+1

            items.append(item)

        return items
        

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    cmis = Cmis()
    if not cmis.login():
        logging.error('cannot login')
        exit(1)

    protodata = datetime.date(2018, 1, 4)

    path = cmis.getDocPath('201800000402',protodata)
    
    files=cmis.getChilds(path)

    for f in files:
        versions = cmis.getVersions(f['cmispath'])
        logging.warning(versions)
        while versions:
            ver = versions.pop()
            logging.warning(ver['version'])

