#!/usr/bin/env python3

import json, sys, getopt, tarfile, tempfile, os, gzip
from datetime import datetime

version = "1.2.0"

def get_log_tar(filename):
    tmpFolder = tempfile.TemporaryDirectory()
    logs = []
    print("TAR: Using temporary folder '{}'".format(tmpFolder))
    with tmpFolder as folder:
        print("TAR: Extracting '{}'".format(filename))
        tar = tarfile.open(filename, "r")
        tar.extractall(path=folder)
        tar.close()

        files = os.listdir(folder)
        print("TAR: Got files: {}".format(files))
        for file in files:
            fileName = os.path.join(folder, file)
            print("TAR: Opening File '{}'".format(fileName))
            logs.extend(get_log_normal(fileName))
    return logs


def get_log_gzip(filename):
    tmpFolder = tempfile.TemporaryDirectory()
    print("GZIP: Reading Compressed '{}'".format(filename))
    file = gzip.open(filename, "rb")
    data = file.read()
    file.close()

    with tmpFolder as folder:
        fileName = os.path.join(folder, "caddy.log")

        print("GZIP: Writing Uncompressed '{}'".format(fileName))
        file = open(fileName, "wb")
        file.write(data)
        file.close()

        print("LOG: Reading JSON '{}'".format(fileName))
        file = open(fileName, "r")

        logs = get_log_file(file)
    return logs

def get_log_normal(filename):
    print("LOG: Reading JSON '{}'".format(filename))
    file = open(filename, "r")
    return get_log_file(file)

def get_log_file(file):
    file.seek(0)
    jsonLog = "["
    lineNum = 1
    numLines = sum(1 for line in file)
    file.seek(0)
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
    elif filename.endswith("gz"):
        return get_log_gzip(filename)
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
    print("CLW: Writing NCSA log '{}'".format(filename))
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
    usageString = "{} -o <outputFile> [-i <inputFile>, -d <inputDir>,..]".format(sys.argv[0])

    inputFiles = []
    outputFile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:d:",["inputfile=","outputfile=","inputdir="])
    except getopt.GetoptError:
        print(usageString)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usageString)
            print("\nAccepted Compressed files: GZIP, TAR, BZ2, LZMA")
            print("Accepted Uncompressed files: Caddy 2 Structured Log")
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
    print("\tVersion {}; Copyright 2015-2020 (c) ATVG-Studios\n".format(version))
    main(sys.argv[1:])
