#!/usr/bin/env python3

import json, sys, getopt, tarfile, tempfile, os
from datetime import datetime

def get_log_tar(filename):
    tmpFolder = tempfile.TemporaryDirectory()
    log = ""
    with tmpFolder as folder:
        tar = tarfile.open(filename, "r")
        tar.extractall(path=folder)
        tar.close()

        log = get_log_normal(os.path.join(folder, os.listdir(folder)[0]))
    return log

def get_log_normal(filename):
    file = open(filename, "r")
    jsonLog = "["
    lineNum = 1
    numLines = sum(1 for line in open(filename, "r"))
    for line in file:
        jsonLog += line
        if lineNum < numLines:
            jsonLog += ","
        lineNum += 1
    file.close()
    jsonLog += "]"
    jsonData = json.loads(jsonLog)
    return jsonData

def get_log(filename):
    if tarfile.is_tarfile(filename):
        return get_log_tar(filename)
    else:
        return get_log_normal(filename)

# Gets a element from a elements list or object, returns "" by default and returns the first item of element by default
def get_element(elements, element, first=True, default=""):
    if not isinstance(elements, (list, object)):
        print("Cannot get element '{}' of non-list and non-object!".format(element))
        exit(1)

    if element in elements:
        if isinstance(element, list) and first:
            return elements[element][0]
        else:
            return elements[element]
    return default

def write_common_log(logs, filename):
    file = open(filename, "w")
    for log in logs:
        timestamp = get_element(log, "ts")
        size = get_element(log, "size")
        status = get_element(log, "status")

        request = get_element(log, "request")
        remoteAddress = get_element(request, "remote_addr").split(":")[0]
        uri = get_element(request, "uri")
        protocol = get_element(request, "proto")
        method = get_element(request, "method")

        headers = get_element(request, "headers")
        userAgent = get_element(headers, "User-Agent")
        referer = get_element(headers, "Referer")

        tls = get_element(request, "tls")
        serverName = get_element(tls, "server_name")

        timestamp = datetime.utcfromtimestamp(timestamp).strftime('%d/%b/%Y:%H:%M:%S')

        # Below is the NCSA vhost format, we transform the Caddy log into this so that goaccess gets the most data
        # %v:%^ %h %^[%d:%t %^] "%r" %s %b "%R" "%u"
        file.write("{}:443 {} [{} +0200] \"{} {} {}\" {} {} \"{}\" \"{}\"\n".format(
            serverName, remoteAddress, timestamp, method, uri, protocol, status, size, referer, userAgent))
    file.close()

def main(argv):
    inputFiles = []
    outputFile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:d:",["inputfile=","outputfile=","inputdir="])
    except getopt.GetoptError:
        print(sys.argv[0] + " -o <outputFile> [-i <inputFile>, -d <inputDir>,..]")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(sys.argv[0] + " -o <outputFile> [-i <inputFile>,..]")
            sys.exit()
        elif opt in ("-i", "--inputfile"):
            inputFiles.append(arg)
        elif opt in ("-o", "--outputfile"):
            outputFile = arg
        elif opt in ("-d", "--inputdir"):
            files = os.listdir(arg)
            for file in files:
                inputFiles.append(os.path.join(arg, file))
    print("Input Files: {}\nOutput File: {}".format(inputFiles, outputFile))

    fullLog = []
    for file in inputFiles:
        if file != outputFile:
            fullLog.extend(get_log(file))
    write_common_log(fullLog, outputFile)

if __name__ == "__main__":
    print("\tCaddy v2 JSON log to NCSA vHost log converter")
    print("\tVersion 1.1.0; Copyright 2015-2020 (c) ATVG-Studios\n")
    main(sys.argv[1:])
