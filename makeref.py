#!/usr/bin/env python

import os, glob


def sortkey(x):
    return os.path.basename(x).lower()

def sort_list_by_keyfunc(alist, akey):
    """ sort(key=sortkey) is only in python2.4.
         this is not inplace like list.sort()
    """
    # make a list of tupples with the key as the first.
    keys_and_list = zip(map(akey, alist), alist)
    keys_and_list.sort()
    alist = map(lambda x:x[1], keys_and_list)
    return alist


def Run():
    # get files and shuffle ordering
    files = glob.glob('src/*.doc') + glob.glob('lib/*.doc')
    files.remove("src/pygame.doc")

    #XXX: sort(key=) is only available in >= python2.4
    #files.sort(key=sortkey)
    files = sort_list_by_keyfunc(files, sortkey)

    files.insert(0, "src/pygame.doc")
    docs = []
    pages = []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        pages.append(name)
        d = name, Doc('', open(f, "U"))
        docs.append(d)
    
    #pages.sort(key=str.lower)
    pages = sort_list_by_keyfunc(pages, str.lower)

    pages.insert(0, "index")
    
    index = {}
    justDocs = []
    for name, doc in docs:
        justDocs.append(doc)
        MakeIndex(name, doc, index)
    
    for name, doc in docs:
        fullname = "docs/ref/%s.html" % name
        outFile = open(fullname, "w")
        outFile.write(HTMLHeader % name)
        WritePageLinks(outFile, pages)
        outFile.write(HTMLMid)
        HtmlOut(doc, index, outFile)
        outFile.write(HTMLFinish)
        outFile.close()
 
    outFile = open("src/pygamedocs.h", "w")
    for doc in justDocs:
        WriteDocHeader(outFile, doc)

    topDoc = LayoutDocs(justDocs)

    outFile = open("docs/ref/index.html", "w")
    outFile.write(HTMLHeader % "Index")
    WritePageLinks(outFile, pages)
    outFile.write(HTMLMid)
    outFile.write("<ul>\n\n")
    WriteIndex(outFile, index, topDoc)
    outFile.write("\n\n</ul>\n")
    outFile.write(HTMLFinish)
    outFile.close()


def HtmlOut(doc, index, f):
    f.write('\n\n<a name="%s">\n' % doc.fullname)
    f.write("<big><b>%s</big></b><br><ul>\n" % doc.fullname)
    if doc.descr:
        f.write("  <i>%s</i><br>\n" % doc.descr) 
    if doc.protos:
        for p in doc.protos:
            f.write("  <tt>%s</tt><br>\n" % p)
    if doc.kids:
        f.write("<ul><small><table>\n")
        for kid in doc.kids:
            f.write("  <tr><td>%s</td><td>%s</td></tr>\n"
                        % (index.get(kid.fullname + "()"), kid.descr or ""))
        f.write("</table></small></ul>\n")
    if doc.docs:
        pre = False
        for d in doc.docs:
            if d[0] == '*':
                f.write("<ul>\n")
                for li in d[1:].split('*'):
                    txt = HtmlPrettyWord(li)
                    f.write(" <li>%s</li>\n" % txt)
                f.write("</ul>\n")
            else:
                txt, pre = HtmlPrettyLine(d, index, pre)
                f.write(txt)
        if pre:
            f.write("</pre>\n")
    else:
        f.write(" &nbsp;<br> \n")

    f.write("<!--COMMENTS:"+doc.fullname+"-->")
    f.write(" &nbsp;<br> \n")
    
    if doc.kids:
        for k in doc.kids:
            HtmlOut(k, index, f)
    f.write("<br></ul>\n")



def HtmlPrettyWord(word):
    if "." in word[:-1] or word.isupper():
        return "<tt>%s</tt>" % word
    return word



def HtmlPrettyLine(line, index, pre):
    pretty = ""
    
    if line[0].isspace():
        if not pre:
            pretty += "<pre>"
            pre = True
    elif pre:
        pre = False
        pretty += "</pre>"
    
    if not pre:
        pretty += "<p>"
        for word in line.split():
            if word[-1] in ",.":
                finish = word[-1]
                word = word[:-1]
            else:
                finish = ""
            link = index.get(word)
            if link:
                pretty += "<tt>%s</tt>%s " % (link, finish)
            elif word.isupper() or "." in word[1:-1]:
                pretty += "<tt>%s</tt>%s " % (word, finish)
            else:
                pretty += "%s%s " % (word, finish)
        pretty += "</p>\n"
    else:
        pretty += line + "\n"
    return pretty, pre



def WritePageLinks(outFile, pages):
    links = []
    for page in pages[1:]:
        link = "<a href=%s.html>%s</a>" % (page, page.title())
        links.append(link)
    outFile.write("&nbsp;||&nbsp;\n".join(links))
    outFile.write("\n</p>\n\n")


def MakeIndex(name, doc, index):
    if doc.fullname:
        link = '<a href="%s.html#%s">%s</a>' % (name, doc.fullname, doc.fullname)
        index[doc.fullname + "()"] = link
    if doc.kids:
        for kid in doc.kids:
            MakeIndex(name, kid, index)


def LayoutDocs(docs):
    levels = {}
    for doc in docs:
        if doc.fullname:
            topName = doc.fullname.split(".")[-1]
            levels[topName] = doc

    top = levels["pygame"]
    for doc in docs:
        if doc is top:
            continue
        parentName = doc.fullname.split(".")[-2]
        parent = levels.get(parentName)
        if parent is not None:
            parent.kids.append(doc)

    return top


def WriteIndex(outFile, index, doc):
    link = index.get(doc.fullname + "()", doc.fullname)
    outFile.write("<li>%s</li>\n" % link)
    if doc.kids:
        outFile.write("<ul>\n")
        sortKids = list(doc.kids)
        sortKids.sort()
        for kid in sortKids:
            WriteIndex(outFile, index, kid)
        outFile.write("</ul>\n")



def WriteDocHeader(f, doc):
    name = doc.fullname.replace(".", "")
    name = name.replace("_", "")
    name = name.upper()
    defineName = "DOC_" + name
    text = ""
    if doc.protos:
        text = "\\n".join(doc.protos)
    if doc.descr:
        if text:
            text += "\\n"
        text += doc.descr
    
    f.write('#define %s "%s"\n\n' % (defineName, text))

    if doc.kids:
        for kid in doc.kids:
            WriteDocHeader(f, kid)


class Doc(object):
    def __init__(self, parentname, f):
        self.kids = None
        self.protos = []
        self.docs = None
        self.descr = ""
        self.name = ""
        self.fullname = ""
        self.finished = False

        curdocline = ""
        while True:
            line = f.readline()
            if not line:
                break
            line = line.rstrip()

            if line == "<END>":
                if curdocline:
                    self.docs.append(curdocline)
                    curdocline = ""
                self.finished = True
                break

            if self.kids is not None:
                kid = Doc(self.fullname, f)
                if kid:
                    self.kids.append(kid)


            if line == "<SECTION>":
                if curdocline:
                    self.docs.append(curdocline)
                    curdocline = ""
                self.kids = []
                continue
            
            if line:
                if self.docs is not None:
                    if line[0].isspace():
                        if curdocline:
                            self.docs.append(curdocline)
                            curdocline = ""
                        self.docs.append(line)
                    else:
                        curdocline += line + " "
                elif not self.name:
                    self.name = line
                    if parentname:
                        splitparent = parentname.split(".")
                        if splitparent[-1][0].isupper():
                            self.fullname = splitparent[-1] + "." + line
                        else:
                            self.fullname = parentname + "." + line
                    else:
                        self.fullname = line
                elif not self.descr:
                    self.descr = line
                else:
                    self.protos.append(line)
            else:
                if self.docs is not None:
                    if curdocline:
                        self.docs.append(curdocline)
                    curdocline = ""
                elif self.name and self.kids is  None:
                    self.docs = []

    def __repr__(self):
        return "<Doc '%s'>" % self.name
            
    def __nonzero__(self):
        return self.finished

    def __cmp__(self, b):
        return cmp(self.name.lower(), b.name.lower())



HTMLHeader = """
<html>
<title>%s - Pygame Documentation</title>
<body bgcolor=#aaeebb text=#000000 link=#331111 vlink=#331111>


<table cellspacing=3 width=100%%><tr><td bgcolor=#00000>
<table width=100%%><tr><td bgcolor=c2fc20 align=center>
    <a href=http://www.pygame.org>
    <img src=../pygame_tiny.gif style='margin: 4px' border=0 width=200 height=60></a><br>
    <b>pygame&nbsp;&nbsp;&nbsp;documentation</b>
</td><td bgcolor=6aee28 align=center valign=top width=100%%>

	||&nbsp;
	<a href=http://www.pygame.org>Pygame Home</a> &nbsp;||&nbsp;
	<a href=../index.html>Help Contents</a> &nbsp;||
	<a href=index.html>Reference Index</a> &nbsp;||
	<br>&nbsp;<br>
	
"""

HTMLMid = """
</td></tr></table></td></tr></table>
<br>
"""

HTMLFinish = """
</body></html>
"""



if __name__ == '__main__':
    Run()

