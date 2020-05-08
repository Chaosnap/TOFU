#!/bin/python3
import re


class vcdException(Exception):
    pass


def buildfromtokens(token):
    collector = []
    while(True):
        current_token = next(token)
        if(current_token == "$end"):
            break
        collector.append(current_token)
    collected = " ".join(collector)
    return collected


def identifierToName(vcdHeader, scope):
    blah = {}
    for var in vcdHeader["scope"][scope]:
        blah[var["identifier"]] = var["name"]
    return blah


fileName = "./dummy-vivado.vcd"
# fileName = "./dummy-modelsim.vcd"
fid = open(fileName)


def token_generator(fid):
    for line in fid:
        for word in line.split():
            yield word


tokens = token_generator(fid)


vcdHeader = {}
vcdHeader["scope"] = {}
currScope = []

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
        vcdHeader["scope"]["->".join(currScope)] = []

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
            # print("width: %s\tidentifier: %s\tname: %s" % (width, identifier, name))
            # print(width)
        else:
            raise vcdException("unable to parse variable: %s" % var)

        vcdHeader["scope"]["->".join(currScope)].append({"name": name, "width": int(width), "identifier": identifier})

    elif(keyword == "$enddefinitions"):
        enddefinition = buildfromtokens(tokens)
        # print("enddefinition: %s" % enddefinition)
        break

    else:
        raise vcdException("undefined keyword: %s" % keyword)


# scope = "module lwc_tb->module uut->module Inst_Cipher"
# fuck the verilog identifiers
scope = "module LWC_TB->module uut->module Inst_Cipher"
blah = identifierToName(vcdHeader, scope)


def iton(x):
    return blah[x]


def bintohex(x):
    print(x)
    if re.match("^([bB][xXzZ]+)$", x):
        return x[1:]
    else:
        return hex(int(x[1:], 2))


# extract simulation values
for current_token in tokens:
    # print(current_token)

    match_time = re.match("^#([0-9]+)$", current_token)
    match_update_scalar = re.match("^([01xXzZ])(.+)$", current_token)
    match_update_vector = re.match("^([bB][01xXzZ]+)$", current_token)
    match_dumpvars = re.match("^(\\$dumpvars)$", current_token)

    if match_time is not None:
        time = int(match_time.groups()[0])
        print("-" * 100)
        print("time: %s" % time)

    elif match_dumpvars is not None:
        # extract initial value
        for dumpvar_token in tokens:
            if(dumpvar_token == "$end"):
                break
            match_dumpvar_scalar = re.match("^([01xXzZ])(.+)$", dumpvar_token)
            match_dumpvar_vector = re.match("^([bB][01xXzZ]+)$", dumpvar_token)
            if match_dumpvar_scalar is not None:
                # update signal values
                val = match_dumpvar_scalar.groups()[0]
                var = match_dumpvar_scalar.groups()[1]
                print("update: %s ---> %s" % (iton(var), val))

            elif match_dumpvar_vector is not None:
                val = match_dumpvar_vector.groups()[0]
                var = next(tokens)
                print("update: %s ---> %s" % (iton(var), val))

            else:
                raise vcdException("unable to parse variable: %s" % dumpvar_token)

    elif match_update_scalar is not None:
        # update signal values
        val = match_update_scalar.groups()[0]
        var = match_update_scalar.groups()[1]
        # update signal values
        print("update: %s ---> %s" % (iton(var), val))

    elif match_update_vector is not None:
        val = match_update_vector.groups()[0]
        var = next(tokens)
        # update signal values
        print("update: %s ---> %s" % (iton(var), val))

    else:
        raise vcdException("unable to parse variable: %s" % current_token)


# print(vcdHeader)
