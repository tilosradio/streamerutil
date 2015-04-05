#!/usr/bin/env python

import os, sys, time, signal, socket, select

hostName = 'stream.tilos.hu'
portNumber = 80
mountPoint = '/tilosklub'
pathPrefix = '/usr/local/www/vhosts/tilos.hu/htdocs/tilosklub/'
secondsToRun = 30 * 60 + 2
#secondsToRun = 20

print 'streamSaver starting up ...'
print 'CWD: %s'%os.getcwd()

def setFileName(pathPrefix = ''):
    year, month, day, hour, min, sec, wday, yday, isdst = time.localtime()
    if not os.path.isdir(os.path.join(pathPrefix, '%s'%year)):
        os.mkdir(os.path.join(pathPrefix, '%s'%year))
    if not os.path.isdir(os.path.join(pathPrefix, '%s'%year, '%02d'%month)):
        os.mkdir(os.path.join(pathPrefix, '%s'%year, '%02d'%month))
    if not os.path.isdir(os.path.join(pathPrefix, '%s'%year, '%02d'%month, '%02d'%day)):
        os.mkdir(os.path.join(pathPrefix, '%s'%year, '%02d'%month, '%02d'%day))

    return os.path.join(pathPrefix, '%s'%year, '%02d'%month, '%02d'%day, 'tilosklub-%02d%02d%02d-%02d%02d.mp3'%(year, month, day, hour, min))

fileName = setFileName(pathPrefix)

def processResponse(header):
    headerList = header.split('\r\n')
    responseCode = int(headerList[0].split(' ')[1])
    return responseCode

def childProcess():
    fileDescriptorList = []
    socketList = []
    def shutDown():
        for element in fileDescriptorList:
            element.close()
        for element in socketList:
            element.close()
    def abortSignal(sigNum, frame):
        print 'shutting down ... '
        shutDown()
        print 'closed descriptors, exiting'
        sys.exit(1)
    signal.signal(signal.SIGTERM, abortSignal)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostName, portNumber))
    sock.send('GET %s HTTP/1.1\nHost: %s\nUser-Agent: Karolyi\'s stream saver\nConnection: close\n\n'%(mountPoint, hostName))
    sock.shutdown(socket.SHUT_WR)
    socketList.append(sock)
    fileDescr = file(fileName, 'ab')
    fileDescriptorList.append(fileDescr)
    data = ''
    headerSent = False
    # TODO: Poll-al megcsinalni
    while True:
#        print 'receiving ...'
        selectTuple = select.select([sock], [], [])
        if len(selectTuple[0]) > 0:
            del(data)
            data = sock.recv(16384)
            if len(data) < 1:
                # Socked disconnected
                shutDown()
                sys.exit(1)
            if not headerSent:
                headerEnd = data.find('\r\n\r\n')
                if headerEnd > -1:
                    print 'header found: %s'%data[:headerEnd + 2]
                    retCode = processResponse(data[:headerEnd + 2])
                    if retCode != 200:
                        print 'retCode %s, not OK'%retCode
                        break
                    data = data[headerEnd + 4:]
                    headerSent = True
            if headerSent:
                fileDescr.write(data)
    print 'child dies'
    shutDown()
    sys.exit(0)

def forkAChild():
    try:
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)

    if pid == 0:
        # Child
        os.setsid()
        childProcess()
    else:
        return pid

def createDaemon():
    pidList = list()
    startedAt = time.time()

    pidList.append(forkAChild())
    print 'child pid: %s'%pidList
    while True:
        for currPid in pidList:
            retTuple = os.waitpid(currPid, os.WNOHANG)
            if retTuple[0] == currPid:
                print time.strftime('%c')
                print '%s exited'%currPid
                del(pidList[pidList.index(currPid)])
                pidList.append(forkAChild())
        time.sleep(1)
        if time.time() - startedAt > secondsToRun:
            break
    for currPid in pidList:
        print 'killing child pid %s'%currPid
        os.kill(currPid, signal.SIGTERM)
    print 'parent quits'
    sys.exit(0)

if __name__ == "__main__":
    retCode = createDaemon()
