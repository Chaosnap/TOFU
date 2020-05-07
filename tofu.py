#!/bin/python3

def buildfromtokens(token):
    collector = []
    while(True):
        current_token = next(token)    
        if(current_token == "$end"):
            break
        collector.append(current_token)
    collected = " ".join(collector)
    return collected

def vcd_date(token):
    collected = buildfromtokens(tokens)
    return collected

def vcd_version(token):
    collected = buildfromtokens(tokens)
    return collected

def vcd_timescale(token):
    collected = buildfromtokens(tokens)
    return collected

def vcd_scope(token):
    collected = buildfromtokens(tokens)
    return collected

def vcd_var(token):
    collected = buildfromtokens(tokens)
    return collected

def vcd_upscope(token):
    collected = buildfromtokens(tokens)
    return collected

def vcd_enddefinitions(token):
    collected = buildfromtokens(tokens)
    return collected

def vcd_comment(token):
    collected = buildfromtokens(tokens)
    return collected

vcd_keywords = {
    "$comment":        vcd_comment,
    "$date":           vcd_date,
    "$enddefinitions": vcd_enddefinitions,
    "$scope":          vcd_scope,
    "$timescale":      vcd_timescale,
    "$upscope":        vcd_upscope,
    "$var":            vcd_var,
    "$version":        vcd_version,
    # "$end":            vcd_end,
}


fid = open("./dummy-vivado.vcd")


def token_generator(fid):
    for line in fid:
        for word in line.split():
            yield word

tokens = token_generator(fid)

while(True):
    # extract informations from value change dump
    
    handler = None
    keyword = None
    try:
        keyword = next(tokens)
        handler = vcd_keywords[keyword]
    except KeyError:
        print("undefined command: %s" % (keyword))
        break

    #process extracted data
    if(keyword == "$date"):
        date = handler(tokens)
        print("date: %s" % date)
    elif(keyword == "$version"):
        version = handler(tokens)
        print("version: %s" % version)
    elif(keyword == "$timescale"):
        timescale = handler(tokens)
        print("timescale: %s" % timescale)
    elif(keyword == "$scope"):
        scope = handler(tokens)
        print("scope: %s" % scope)
    elif(keyword == "$var"):
        var = handler(tokens)
        print("var: %s" % var)
    elif(keyword == "$upscope"):
        print("upscope")
        handler(tokens)
    elif(keyword == "$enddefinitions"):
        print("enddefinition")
        enddefinition = handler(tokens)
        print("enddefinition: %s" % enddefinition)
    else:
        break