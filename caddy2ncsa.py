#!/usr/bin/env python3

import json, sys, getopt
from datetime import datetime

def get_log(filename):
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

# Gets a 
def get_element(elements, element, first=True):
    if not isinstance(elements, (list, object)):
        print("Cannot get element '{}' of non-list and non-object!".format(element))
        exit(1)

    if element in elements:
        if isinstance(element, list) and first:
            return elements[element][0]
        else:
            return elements[element]
    return ""

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
        opts, args = getopt.getopt(argv,"hi:o:",["inputfile=","outputfile="])
    except getopt.GetoptError:
        print(sys.argv[0] + " -o <outputFile> [-i <inputFile>,..]")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(sys.argv[0] + " -o <outputFile> [-i <inputFile>,..]")
            sys.exit()
        elif opt in ("-i", "--inputfile"):
            inputFiles.append(arg)
        elif opt in ("-o", "--outputfile"):
            outputFile = arg
    print("Input Files: {}\nOutput File: {}".format(inputFiles, outputFile))

    fullLog = []
    for file in inputFiles:
        fullLog.extend(get_log(file))
    write_common_log(fullLog, outputFile)

if __name__ == "__main__":
    print("\tCaddy v2 JSON log to NCSA vHost log converter")
    print("\tVersion 1.0; Copyright 2015-2020 (c) ATVG-Studios\n")
    main(sys.argv[1:])
