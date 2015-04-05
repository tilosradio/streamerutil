#!/usr/bin/env python

import os, sys, _mysql


class LogLoader:
    logFileName = '/usr/local/www/var/log/archive.tilos.hu-access.log'
    archivePath = '/usr/local/www/vhosts/archive.tilos.hu/htdocs'
    fileSizeDict = dict()
    requestDict = dict()
    resultList = list()

    def escapeChars(self, text):
        return text.replace('\'', '\\\'')

    def processFileName(self, requestName):
        archiveNameList = requestName.split('-')
        if len(archiveNameList) == 3:
            return '%s%s'%(archiveNameList[1], archiveNameList[2][:4])
        return False

    def processLine(self, line):
        lineList = line.split(' ')
        # Response code
        if int(lineList[8]) in [304, 206, 200]:
            # Does the file exist?
            fileName = self.processFileName(lineList[6])
            if not self.fileSizeDict.has_key(fileName):
                try:
                    fileSize = os.path.getsize(os.path.join(self.archivePath, lineList[6][1:]))
                    self.fileSizeDict[fileName] = fileSize
                except OSError:
                    pass
            if self.fileSizeDict.has_key(fileName):
                # File exists
                self.resultList.append([fileName, lineList[8], lineList[-1]])

    def processStats(self):
        dataForDatabaseDict = dict()
        for fileName, responseCode, servedBytes in self.resultList:
            responseCodeDict = dataForDatabaseDict.get(fileName, dict())
            responseCodeStatDict = responseCodeDict.get(responseCode, dict())
            newServedBytes = responseCodeStatDict.get('servedBytes', 0) + int(servedBytes)
            newHitCount = responseCodeStatDict.get('hitCount', 0) + 1
            responseCodeStatDict.update({'servedBytes' : newServedBytes, 'hitCount' : newHitCount})
            responseCodeDict.update({responseCode : responseCodeStatDict})
            dataForDatabaseDict.update({fileName : responseCodeDict})
        self.requestDict = dataForDatabaseDict

    def doDatabase(self):
        dbConn = _mysql.connect(host = '127.0.0.3', user = 'archiveStat', passwd = 'thei8Ahh', db = 'archiveStat')

        # Do filesizes first
        for fileName in self.fileSizeDict:
            fileSize = str(self.fileSizeDict[fileName])
            dbConn.query("REPLACE INTO fileSizes SET fileName = '%s', fileSize = '%s'"%(self.escapeChars(fileName), self.escapeChars(fileSize)))

        # Do requests
        for fileName in self.requestDict:
            for responseCode in self.requestDict[fileName]:
                servedBytes = self.requestDict[fileName][responseCode]['servedBytes']
                hitCount = self.requestDict[fileName][responseCode]['hitCount']
                # Select if this record exists
                dbConn.query("SELECT fileName FROM requestData WHERE fileName = '%s' AND responseCode = '%s'"%(self.escapeChars(fileName), self.escapeChars(responseCode)))
                result = dbConn.store_result()
                if result.num_rows() == 0:
                    query = ("INSERT INTO requestData SET fileName = '%s', responseCode = '%s', hitCount = '%s', servedBytes = '%s'"%(
                        self.escapeChars(fileName),
                        self.escapeChars(responseCode),
                        hitCount,
                        servedBytes
                    ))
                    # print query
                    dbConn.query(query)
                else:
                    query = ("UPDATE requestData SET hitCount = hitCount + %s, servedBytes = servedBytes + %s WHERE fileName = '%s' AND responseCode = '%s'"%(
                        hitCount,
                        servedBytes,
                        self.escapeChars(fileName),
                        self.escapeChars(responseCode)
                    ))
                    # print query
                    dbConn.query(query)
        dbConn.close()

    def run(self):
        os.chdir(os.path.dirname(sys.argv[0]))
        with open('archiveStat.dat') as posFileDescriptor:
            filePos = int(posFileDescriptor.read())
        fileDescriptor = open(self.logFileName)
        if os.path.getsize(self.logFileName) >= filePos:
            # Only do incremental analyzing if file is bigger then the latest filePos, else analyzing will start from the beginning.
            # This is useful for switched logs.
            fileDescriptor.seek(filePos)
        for line in fileDescriptor:
            if line.find('"GET /online/') > -1 and line.find('filename') == -1:
                if line.find('0.mp3 HTTP/1." ') > -1:
                    # Line matches
                    self.processLine(line.strip())
        filePos = fileDescriptor.tell()
        with open('archiveStat.dat', 'w') as posFileDescriptor:
            posFileDescriptor.write(str(filePos))
        fileDescriptor.close()
        self.processStats()
        self.doDatabase()

logLoader = LogLoader()

logLoader.run()
