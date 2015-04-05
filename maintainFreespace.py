#!/usr/bin/env python

import os, glob


mountPoint = '/home/ujtilos'
freeUpUnderThisPercent = 3
filePath = '/home/ujtilos/htdocs/online/'
filesList = list()

def listRecursive(path):
    filesInDir = glob.glob(os.path.join(path, '*'))
    if filesInDir is None:
        filesInDir = list()
    for fileName in filesInDir:
        if os.path.isdir(os.path.join(path, fileName)):
            listRecursive(os.path.join(path, fileName))
        elif os.path.isfile(os.path.join(path, fileName)):
            filesList.append(os.path.join(path, fileName))

def listFiles():
    listRecursive(filePath)
    filesList.sort()

def getFreeSpacePercent():
    stat = os.statvfs(mountPoint)
    freeBytes = float(stat.f_bsize * stat.f_bavail)
    totalBytes = float(stat.f_bsize * stat.f_blocks)
    percentage = int(freeBytes / totalBytes * 10000) / float(100)
    return percentage

def eraseEmptyDirs(fileInDir):
    # Day name
    dirName = os.path.dirname(fileInDir)
    dirFileCount = len(glob.glob(os.path.join(dirName, '*')))
    if dirFileCount == 0 and os.path.isdir(dirName):
        print '%s is empty, removing.'%dirName
        os.rmdir(dirName)
    # Month name
    dirname = os.path.dirname(dirName)
    dirFileCount = len(glob.glob(os.path.join(dirName, '*')))
    if dirFileCount == 0 and os.path.isdir(dirName):
        print '%s is empty, removing.'%dirName
        os.rmdir(dirName)
    # Year name
    dirname = os.path.dirname(dirName)
    dirFileCount = len(glob.glob(os.path.join(dirName, '*')))
    if dirFileCount == 0 and os.path.isdir(dirName):
        print '%s is empty, removing.'%dirName
        os.rmdir(dirName)

def run():
    percentage = getFreeSpacePercent()
    listFiles()
    while percentage < freeUpUnderThisPercent:
        fileToRemove = filesList.pop(0)
        print 'Free space is %s%%, removing %s'%(percentage, fileToRemove)
        os.unlink(fileToRemove)
        eraseEmptyDirs(fileToRemove)
        percentage = getFreeSpacePercent()

run()
