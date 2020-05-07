#!/bin/python3
import re


class vcdException(Exception):
    pass


vcdHeader = {}
vcdHeader["scope"] = {}
currScope = []


def buildfromtokens(token):
    collector = []
    while(True):
        current_token = next(token)
        if(current_token == "$end"):
            break
        collector.append(current_token)
    collected = " ".join(collector)
    return collected


# fileName = "./dummy-vivado.vcd"
fileName = "./dummy-modelsim.vcd"
fid = open(fileName)


def token_generator(fid):
    for line in fid:
        for word in line.split():
            yield word


tokens = token_generator(fid)

# extract header
while(True):
    # extract header from value change dump
    keyword = next(tokens)
    # process extracted data
    if(keyword == "$comment"):
        comment = buildfromtokens(tokens)
        # print("comment: %s" % comment)
        vcdHeader[keyword[1:]] = comment

    if(keyword == "$date"):
        date = buildfromtokens(tokens)
        # print("date: %s" % date)
        vcdHeader[keyword[1:]] = date

    elif(keyword == "$version"):
        version = buildfromtokens(tokens)
        # print("version: %s" % version)
        vcdHeader[keyword[1:]] = version

    elif(keyword == "$timescale"):
        timescale = buildfromtokens(tokens)
        # print("timescale: %s" % timescale)
        vcdHeader[keyword[1:]] = timescale

    elif(keyword == "$scope"):
        scope = buildfromtokens(tokens)
        currScope.append(scope)
        # print("->".join(currScope))
        vcdHeader["scope"]["->".join(currScope)] = {}

    elif(keyword == "$upscope"):
        upscope = buildfromtokens(tokens)
        # print("upscope: %s" % upscope)
        currScope.pop()

    elif(keyword == "$var"):
        var = buildfromtokens(tokens)
        # print("var: %s" % var)
        match = re.match("^wire\\s+([0-9]+)\\s+(\\S*)\\s+(.*)$", var)
        if match is not None:
            width = match.groups()[0]
            identifier = match.groups()[1]
            name = match.groups()[2]
            print("width: %s\tidentifier: %s\tname: %s" %
                  (width, identifier, name))
            # print(width)
        else:
            raise vcdException("unable to parse variable: %s" % var)

        vcdHeader["scope"]["->".join(currScope)][name] = {"width": int(width), "identifier": identifier}

    elif(keyword == "$enddefinitions"):
        enddefinition = buildfromtokens(tokens)
        # print("enddefinition: %s" % enddefinition)
        break

    else:
        raise vcdException("undefined keyword: %s" % keyword)


# extract simulation values
for current_token in tokens:
    # print(current_token)

    match_time = re.match("^#([0-9]+)$", current_token)
    match_update_scalar = re.match("^([01xXzZ])(.+)$", current_token)
    match_update_vector = re.match("^([bB][01]+)$", current_token)
    match_dumpvars = re.match("^(\\$dumpvars)$", current_token)

    if match_time is not None:
        time = int(match_time.groups()[0])
        # print("time: %s" % time)
    
    elif match_dumpvars is not None:
        #extract initial value
        #das fehlt noch
        while(True):
            current_token = next(tokens)
            if(current_token == "$end"):
                break
    elif match_update_scalar is not None:
        #update signal values
        # print(current_token)
        pass
    elif match_update_vector is not None:
        # print(current_token + " ",end="")
        foo = next(tokens)
        # print(next(foo))
        #update signal values
        pass

    else:
        raise vcdException("unable to parse variable: %s" % current_token)


# print(vcdHeader)
