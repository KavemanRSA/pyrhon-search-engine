def build_index():

    import sys, os, re
    import time, string
    from math import log

    # Define global variables used as counters
    tokens = 0
    documents = 0
    terms = 0
    termindex = 0
    docindex = 0
    stop_words_count = 0

    # Capture the start time of the routine so that we can determine the total running
    # time required to process the corpus
    t2 = time.localtime()

    class PorterStemmer:

        def __init__(self):
            self.b = ""  # buffer for word to be stemmed
            self.k = 0
            self.k0 = 0
            self.j = 0   # j is a general offset into the string

        def cons(self, i):
            if self.b[i] == 'a' or self.b[i] == 'e' or self.b[i] == 'i' or self.b[i] == 'o' or self.b[i] == 'u':
                return 0
            if self.b[i] == 'y':
                if i == self.k0:
                    return 1
                else:
                    return (not self.cons(i - 1))
            return 1

        def m(self):
            n = 0
            i = self.k0
            while 1:
                if i > self.j:
                    return n
                if not self.cons(i):
                    break
                i = i + 1
            i = i + 1
            while 1:
                while 1:
                    if i > self.j:
                        return n
                    if self.cons(i):
                        break
                    i = i + 1
                i = i + 1
                n = n + 1
                while 1:
                    if i > self.j:
                        return n
                    if not self.cons(i):
                        break
                    i = i + 1
                i = i + 1

        def vowelinstem(self):
            for i in range(self.k0, self.j + 1):
                if not self.cons(i):
                    return 1
            return 0

        def doublec(self, j):
            if j < (self.k0 + 1):
                return 0
            if (self.b[j] != self.b[j-1]):
                return 0
            return self.cons(j)

        def cvc(self, i):
            if i < (self.k0 + 2) or not self.cons(i) or self.cons(i-1) or not self.cons(i-2):
                return 0
            ch = self.b[i]
            if ch == 'w' or ch == 'x' or ch == 'y':
                return 0
            return 1

        def ends(self, s):
            length = len(s)
            if s[length - 1] != self.b[self.k]: # tiny speed-up
                return 0
            if length > (self.k - self.k0 + 1):
                return 0
            if self.b[self.k-length+1:self.k+1] != s:
                return 0
            self.j = self.k - length
            return 1

        def setto(self, s):
            length = len(s)
            self.b = self.b[:self.j+1] + s + self.b[self.j+length+1:]
            self.k = self.j + length

        def r(self, s):
            if self.m() > 0:
                self.setto(s)

        def step1ab(self):
            if self.b[self.k] == 's':
                if self.ends("sses"):
                    self.k = self.k - 2
                elif self.ends("ies"):
                    self.setto("i")
                elif self.b[self.k - 1] != 's':
                    self.k = self.k - 1
            if self.ends("eed"):
                if self.m() > 0:
                    self.k = self.k - 1
            elif (self.ends("ed") or self.ends("ing")) and self.vowelinstem():
                self.k = self.j
                if self.ends("at"):   self.setto("ate")
                elif self.ends("bl"): self.setto("ble")
                elif self.ends("iz"): self.setto("ize")
                elif self.doublec(self.k):
                    self.k = self.k - 1
                    ch = self.b[self.k]
                    if ch == 'l' or ch == 's' or ch == 'z':
                        self.k = self.k + 1
                elif (self.m() == 1 and self.cvc(self.k)):
                    self.setto("e")

        def step1c(self):
            if (self.ends("y") and self.vowelinstem()):
                self.b = self.b[:self.k] + 'i' + self.b[self.k+1:]

        def step2(self):
            if self.b[self.k - 1] == 'a':
                if self.ends("ational"):   self.r("ate")
                elif self.ends("tional"):  self.r("tion")
            elif self.b[self.k - 1] == 'c':
                if self.ends("enci"):      self.r("ence")
                elif self.ends("anci"):    self.r("ance")
            elif self.b[self.k - 1] == 'e':
                if self.ends("izer"):      self.r("ize")
            elif self.b[self.k - 1] == 'l':
                if self.ends("bli"):       self.r("ble") # --DEPARTURE--
                # To match the published algorithm, replace this phrase with
                #   if self.ends("abli"):      self.r("able")
                elif self.ends("alli"):    self.r("al")
                elif self.ends("entli"):   self.r("ent")
                elif self.ends("eli"):     self.r("e")
                elif self.ends("ousli"):   self.r("ous")
            elif self.b[self.k - 1] == 'o':
                if self.ends("ization"):   self.r("ize")
                elif self.ends("ation"):   self.r("ate")
                elif self.ends("ator"):    self.r("ate")
            elif self.b[self.k - 1] == 's':
                if self.ends("alism"):     self.r("al")
                elif self.ends("iveness"): self.r("ive")
                elif self.ends("fulness"): self.r("ful")
                elif self.ends("ousness"): self.r("ous")
            elif self.b[self.k - 1] == 't':
                if self.ends("aliti"):     self.r("al")
                elif self.ends("iviti"):   self.r("ive")
                elif self.ends("biliti"):  self.r("ble")
            elif self.b[self.k - 1] == 'g': # --DEPARTURE--
                if self.ends("logi"):      self.r("log")
            # To match the published algorithm, delete this phrase

        def step3(self):
            if self.b[self.k] == 'e':
                if self.ends("icate"):     self.r("ic")
                elif self.ends("ative"):   self.r("")
                elif self.ends("alize"):   self.r("al")
            elif self.b[self.k] == 'i':
                if self.ends("iciti"):     self.r("ic")
            elif self.b[self.k] == 'l':
                if self.ends("ical"):      self.r("ic")
                elif self.ends("ful"):     self.r("")
            elif self.b[self.k] == 's':
                if self.ends("ness"):      self.r("")

        def step4(self):
            if self.b[self.k - 1] == 'a':
                if self.ends("al"): pass
                else: return
            elif self.b[self.k - 1] == 'c':
                if self.ends("ance"): pass
                elif self.ends("ence"): pass
                else: return
            elif self.b[self.k - 1] == 'e':
                if self.ends("er"): pass
                else: return
            elif self.b[self.k - 1] == 'i':
                if self.ends("ic"): pass
                else: return
            elif self.b[self.k - 1] == 'l':
                if self.ends("able"): pass
                elif self.ends("ible"): pass
                else: return
            elif self.b[self.k - 1] == 'n':
                if self.ends("ant"): pass
                elif self.ends("ement"): pass
                elif self.ends("ment"): pass
                elif self.ends("ent"): pass
                else: return
            elif self.b[self.k - 1] == 'o':
                if self.ends("ion") and (self.b[self.j] == 's' or self.b[self.j] == 't'): pass
                elif self.ends("ou"): pass
                # takes care of -ous
                else: return
            elif self.b[self.k - 1] == 's':
                if self.ends("ism"): pass
                else: return
            elif self.b[self.k - 1] == 't':
                if self.ends("ate"): pass
                elif self.ends("iti"): pass
                else: return
            elif self.b[self.k - 1] == 'u':
                if self.ends("ous"): pass
                else: return
            elif self.b[self.k - 1] == 'v':
                if self.ends("ive"): pass
                else: return
            elif self.b[self.k - 1] == 'z':
                if self.ends("ize"): pass
                else: return
            else:
                return
            if self.m() > 1:
                self.k = self.j

        def step5(self):
            self.j = self.k
            if self.b[self.k] == 'e':
                a = self.m()
                if a > 1 or (a == 1 and not self.cvc(self.k-1)):
                    self.k = self.k - 1
            if self.b[self.k] == 'l' and self.doublec(self.k) and self.m() > 1:
                self.k = self.k -1

        def stem(self, p, i, j):
            # copy the parameters into statics
            self.b = p
            self.k = j
            self.k0 = i
            if self.k <= self.k0 + 1:
                return self.b # --DEPARTURE--

            # With this line, strings of length 1 or 2 don't go through the
            # stemming process, although no mention is made of this in the
            # published algorithm. Remove the line to match the published
            # algorithm.

            self.step1ab()
            self.step1c()
            self.step2()
            self.step3()
            self.step4()
            self.step5()
            return self.b[self.k0:self.k+1]



    # A Function that removes "stopwords" from a "list" and applies stemming
    def remove_stopwords_and_stem(list, stopwords):
        processed_list = []
        stem = PorterStemmer()
        global stop_words_count
        for word in list:
            if word not in stopwords:
                processed_list.append(stem.stem(word, 0, len(word) - 1))
            else:
                stop_words_count += 1
        return processed_list

    # Set the name of the directory for the corpus
    if len(sys.argv) > 1:
        dirname = sys.argv[1]
    else:
        dirname = input("Enter corpus directory path: ").strip()

    if not os.path.isdir(dirname):
        print("Error: Directory does not exist.")
        exit()

    # Initialize list variables
    alltokens = []
    alldocs = []

    # For each document in the directory read the document into a lower case normalized string
    # after removing tokens beginning with punctuation
    all = [f for f in os.listdir(dirname)]
    for f in all:
        documents += 1
        with open(dirname + '/' + f, 'r') as myfile:
            alldocs.append(f)
            data = myfile.read().replace('\n', ' ').lower()
            for token in data.split():
                if token[0] not in string.punctuation and not token.isdigit() and not len(token) < 2:
                    alltokens.append(token)
                    tokens += 1

    # Comprehensive alphabetically ordered list of 1296 stopwords.
    # Hardcoding this list allows for editability & ensures code can run offline
    # (Source: Igor Brigadir (2019), https://github.com/igorbrigadir/stopwords/blob/master/en/alir3z4.txt)
    mixed_source_stopwords = ["'ll", "'tis", "'twas", "'ve", "a", "a's", "able", "ableabout", "about", "above", "abroad", "abst", "accordance", "according", "accordingly", "across", "act", "actually", "ad", "added", "adj", "adopted", "ae", "af", "affected", "affecting", "affects", "after", "afterwards", "ag", "again", "against", "ago", "ah", "ahead", "ai", "ain't", "aint", "al", "all", "allow", "allows", "almost", "alone", "along", "alongside", "already", "also", "although", "always", "am", "amid", "amidst", "among", "amongst", "amoungst", "amount", "an", 
                            "and", "announce", "another", "any", "anybody", "anyhow", "anymore", "anyone", "anything", "anyway", "anyways", "anywhere", "ao", "apart", "apparently", "appear", "appreciate", "appropriate", "approximately", "aq", "ar", "are", "area", "areas", "aren", "aren't", "arent", "arise", "around", "arpa", "as", "aside", "ask", "asked", "asking", "asks", "associated", "at", "au", "auth", "available", "aw", "away", "awfully", "az", "b", "ba", "back", "backed", "backing", "backs", "backward", "backwards", "bb", "bd", "be", "became", 
                            "because", "become", "becomes", "becoming", "been", "before", "beforehand", "began", "begin", "beginning", "beginnings", "begins", "behind", "being", "beings", "believe", "below", "beside", "besides", "best", "better", "between", "beyond", "bf", "bg", "bh", "bi", "big", "bill", "billion", "biol", "bj", "bm", "bn", "bo", "both", "bottom", "br", "brief", "briefly", "bs", "bt", "but", "buy", "bv", "bw", "by", "bz", "c", "c'mon", "c's", "ca", "call", "came", "can", "can't", "cannot", "cant", "caption", "case", "cases", "cause", 
                            "causes", "cc", "cd", "certain", "certainly", "cf", "cg", "ch", "changes", "ci", "ck", "cl", "clear", "clearly", "click", "cm", "cmon", "cn", "co", "co.", "com", "come", "comes", "computer", "con", "concerning", "consequently", "consider", "considering", "contain", "containing", "contains", "copy", "corresponding", "could", "could've", "couldn", "couldn't", "couldnt", "course", "cr", "cry", "cs", "cu", "currently", "cv", "cx", "cy", "cz", "d", "dare", "daren't", "darent", "date", "de", "dear", "definitely", "describe", "described", 
                            "despite", "detail", "did", "didn", "didn't", "didnt", "differ", "different", "differently", "directly", "dj", "dk", "dm", "do", "does", "doesn", "doesn't", "doesnt", "doing", "don", "don't", "done", "dont", "doubtful", "down", "downed", "downing", "downs", "downwards", "due", "during", "dz", "e", "each", "early", "ec", "ed", "edu", "ee", "effect", "eg", "eh", "eight", "eighty", "either", "eleven", "else", "elsewhere", "empty", "end", "ended", "ending", "ends", "enough", "entirely", "er", "es", "especially", "et", "et-al", "etc", 
                            "even", "evenly", "ever", "evermore", "every", "everybody", "everyone", "everything", "everywhere", "ex", "exactly", "example", "except", "f", "face", "faces", "fact", "facts", "fairly", "far", "farther", "felt", "few", "fewer", "ff", "fi", "fifteen", "fifth", "fifty", "fify", "fill", "find", "finds", "fire", "first", "five", "fix", "fj", "fk", "fm", "fo", "followed", "following", "follows", "for", "forever", "former", "formerly", "forth", "forty", "forward", "found", "four", "fr", "free", "from", "front", "full", "fully", "further", 
                            "furthered", "furthering", "furthermore", "furthers", "fx", "g", "ga", "gave", "gb", "gd", "ge", "general", "generally", "get", "gets", "getting", "gf", "gg", "gh", "gi", "give", "given", "gives", "giving", "gl", "gm", "gmt", "gn", "go", "goes", "going", "gone", "good", "goods", "got", "gotten", "gov", "gp", "gq", "gr", "great", "greater", "greatest", "greetings", "group", "grouped", "grouping", "groups", "gs", "gt", "gu", "gw", "gy", "h", "had", "hadn't", "hadnt", "half", "happens", "hardly", "has", "hasn", "hasn't", "hasnt", "have", 
                            "haven", "haven't", "havent", "having", "he", "he'd", "he'll", "he's", "hed", "hell", "hello", "help", "hence", "her", "here", "here's", "hereafter", "hereby", "herein", "heres", "hereupon", "hers", "herself", "herse”", "hes", "hi", "hid", "high", "higher", "highest", "him", "himself", "himse”", "his", "hither", "hk", "hm", "hn", "home", "homepage", "hopefully", "how", "how'd", "how'll", "how's", "howbeit", "however", "hr", "ht", "htm", "html", "http", "hu", "hundred", "i", "i'd", "i'll", "i'm", "i've", "i.e.", "id", "ie", "if", 
                            "ignored", "ii", "il", "ill", "im", "immediate", "immediately", "importance", "important", "in", "inasmuch", "inc", "inc.", "indeed", "index", "indicate", "indicated", "indicates", "information", "inner", "inside", "insofar", "instead", "int", "interest", "interested", "interesting", "interests", "into", "invention", "inward", "io", "iq", "ir", "is", "isn", "isn't", "isnt", "it", "it'd", "it'll", "it's", "itd", "itll", "its", "itself", "itse”", "ive", "j", "je", "jm", "jo", "join", "jp", "just", "k", "ke", "keep", "keeps", "kept", 
                            "keys", "kg", "kh", "ki", "kind", "km", "kn", "knew", "know", "known", "knows", "kp", "kr", "kw", "ky", "kz", "l", "la", "large", "largely", "last", "lately", "later", "latest", "latter", "latterly", "lb", "lc", "least", "length", "less", "lest", "let", "let's", "lets", "li", "like", "liked", "likely", "likewise", "line", "little", "lk", "ll", "long", "longer", "longest", "look", "looking", "looks", "low", "lower", "lr", "ls", "lt", "ltd", "lu", "lv", "ly", "m", "ma", "made", "mainly", "make", "makes", "making", "man", "many", "may", 
                            "maybe", "mayn't", "maynt", "mc", "md", "me", "mean", "means", "meantime", "meanwhile", "member", "members", "men", "merely", "mg", "mh", "microsoft", "might", "might've", "mightn't", "mightnt", "mil", "mill", "million", "mine", "minus", "miss", "mk", "ml", "mm", "mn", "mo", "more", "moreover", "most", "mostly", "move", "mp", "mq", "mr", "mrs", "ms", "msie", "mt", "mu", "much", "mug", "must", "must've", "mustn't", "mustnt", "mv", "mw", "mx", "my", "myself", "myse”", "mz", "n", "na", "name", "namely", "nay", "nc", "nd", "ne", "near", 
                            "nearly", "necessarily", "necessary", "need", "needed", "needing", "needn't", "neednt", "needs", "neither", "net", "netscape", "never", "neverf", "neverless", "nevertheless", "new", "newer", "newest", "next", "nf", "ng", "ni", "nine", "ninety", "nl", "no", "no-one", "nobody", "non", "none", "nonetheless", "noone", "nor", "normally", "nos", "not", "noted", "nothing", "notwithstanding", "novel", "now", "nowhere", "np", "nr", "nu", "null", "number", "numbers", "nz", "o", "obtain", "obtained", "obviously", "of", "off", "often", "oh", "ok", 
                            "okay", "old", "older", "oldest", "om", "omitted", "on", "once", "one", "one's", "ones", "only", "onto", "open", "opened", "opening", "opens", "opposite", "or", "ord", "order", "ordered", "ordering", "orders", "org", "other", "others", "otherwise", "ought", "oughtn't", "oughtnt", "our", "ours", "ourselves", "out", "outside", "over", "overall", "owing", "own", "p", "pa", "page", "pages", "part", "parted", "particular", "particularly", "parting", "parts", "past", "pe", "per", "perhaps", "pf", "pg", "ph", "pk", "pl", "place", "placed", 
                            "places", "please", "plus", "pmid", "pn", "pm", "point", "pointed", "pointing", "points", "poorly", "possible", "possibly", "potentially", "pp", "pr", "predominantly", "present", "presented", "presenting", "presents", "presumably", "previously", "primarily", "probably", "problem", "problems", "promptly", "proud", "provided", "provides", "pt", "put", "puts", "pw", "py", "q", "qa", "que", "quickly", "quite", "qv", "r", "ran", "rather", "rd", "re", "readily", "really", "reasonably", "recent", "recently", "ref", "refs", "regarding", 
                            "regardless", "regards", "related", "relatively", "research", "reserved", "respectively", "resulted", "resulting", "results", "right", "ring", "ro", "room", "rooms", "round", "ru", "run", "rw", "s", "sa", "said", "same", "saw", "say", "saying", "says", "sb", "sc", "sd", "se", "sec", "second", "secondly", "seconds", "section", "see", "seeing", "seem", "seemed", "seeming", "seems", "seen", "sees", "self", "selves", "sensible", "sent", "serious", "seriously", "seven", "seventy", "several", "sg", "sh", "shall", "shan't", "shant", 
                            "she", "she'd", "she'll", "she's", "shed", "shell", "shes", "should", "should've", "shouldn", "shouldn't", "shouldnt", "show", "showed", "showing", "shown", "showns", "shows", "si", "side", "sides", "significant", "significantly", "similar", "similarly", "since", "sincere", "site", "six", "sixty", "sj", "sk", "sl", "slightly", "sm", "small", "smaller", "smallest", "sn", "so", "some", "somebody", "someday", "somehow", "someone", "somethan", "something", "sometime", "sometimes", "somewhat", "somewhere", "soon", "sorry", "specifically", 
                            "specified", "specify", "specifying", "sr", "st", "state", "states", "still", "stop", "strongly", "su", "sub", "substantially", "successfully", "such", "sufficiently", "suggest", "sup", "sure", "sv", "sy", "system", "sz", "t", "t's", "take", "taken", "taking", "tc", "td", "tell", "ten", "tends", "test", "text", "tf", "tg", "th", "than", "thank", "thanks", "thanx", "that", "that'll", "that's", "that've", "thatll", "thats", "thatve", "the", "their", "theirs", "them", "themselves", "then", "thence", "there", "there'd", "there'll", 
                            "there're", "there's", "there've", "thereafter", "thereby", "thered", "therefore", "therein", "therell", "thereof", "therere", "theres", "thereto", "thereupon", "thereve", "these", "they", "they'd", "they'll", "they're", "they've", "theyd", "theyll", "theyre", "theyve", "thick", "thin", "thing", "things", "think", "thinks", "third", "thirty", "this", "thorough", "thoroughly", "those", "thou", "though", "thoughh", "thought", "thoughts", "thousand", "three", "throug", "through", "throughout", "thru", "thus", "til", "till", "tip", "tis", 
                            "tj", "tk", "tm", "tn", "to", "today", "together", "too", "took", "top", "toward", "towards", "tp", "tr", "tried", "tries", "trillion", "truly", "try", "trying", "ts", "tt", "turn", "turned", "turning", "turns", "tv", "tw", "twas", "twelve", "twenty", "twice", "two", "tz", "u", "ua", "ug", "uk", "um", "un", "under", "underneath", "undoing", "unfortunately", "unless", "unlike", "unlikely", "until", "unto", "up", "upon", "ups", "upwards", "us", "use", "used", "useful", "usefully", "usefulness", "uses", "using", "usually", "uucp", "uy", 
                            "uz", "v", "va", "value", "various", "vc", "ve", "versus", "very", "vg", "vi", "via", "viz", "vn", "vol", "vols", "vs", "vu", "w", "want", "wanted", "wanting", "wants", "was", "wasn", "wasn't", "wasnt", "way", "ways", "we", "we'd", "we'll", "we're", "we've", "web", "webpage", "website", "wed", "welcome", "well", "wells", "went", "were", "weren", "weren't", "werent", "weve", "wf", "what", "what'd", "what'll", "what's", "what've", "whatever", "whatll", "whats", "whatve", "when", "when'd", "when'll", "when's", "whence", "whenever", "where", 
                            "where'd", "where'll", "where's", "whereafter", "whereas", "whereby", "wherein", "wheres", "whereupon", "wherever", "whether", "which", "whichever", "while", "whilst", "whim", "whither", "who", "who'd", "who'll", "who's", "whod", "whoever", "whole", "wholl", "whom", "whomever", "whos", "whose", "why", "why'd", "why'll", "why's", "widely", "width", "will", "willing", "wish", "with", "within", "without", "won", "won't", "wonder", "wont", "words", "work", "worked", "working", "works", "world", "would", "would've", "wouldn", "wouldn't", 
                            "wouldnt", "ws", "www", "x", "y", "ye", "year", "years", "yes", "yet", "you", "you'd", "you'll", "you're", "you've", "youd", "youll", "young", "younger", "youngest", "your", "youre", "yours", "yourself", "yourselves", "youve", "yt", "yu", "z", "za", "zero", "zm", "zr"]
    # Removing stopwords from all tokens
    alltokens = remove_stopwords_and_stem(alltokens, mixed_source_stopwords)


    # Open for write a file for the document dictionary
    #
    documentfile = open(dirname+'/'+'documents.dat', 'w')
    alldocs.sort()
    for f in alldocs:
        docindex += 1
        documentfile.write(f+','+str(docindex)+os.linesep)
    documentfile.close()



    # Open for write a file for the document dictionary
    documentfile = open(dirname + '/' + 'Document Dictionary.dat', 'w')
    alldocs.sort()
    for f in alldocs:
        docindex += 1
        documentfile.write(f + ',' + str(docindex) + os.linesep)
    documentfile.close()

    # Sort the tokens in the list
    alltokens.sort()

    # Define a list for the unique terms
    g = []

    # Identify unique terms in the corpus
    for i in alltokens:
        if i not in g:
            g.append(i)
            terms += 1


    # Output Index to disk file. As part of this process we assign an 'index' number to each unique term.  
    # 
    indexfile = open(dirname+'/'+'index.dat', 'w')
    for i in g:
        termindex += 1
        indexfile.write(i+','+str(termindex)+os.linesep)
    indexfile.close()


    # Output Index to disk file. As part of this process we assign an 'index' number to each unique term.
    indexfile = open(dirname + '/' + 'Term Dictionary.dat', 'w')
    for i in g:
        termindex += 1
        indexfile.write(i + ',' + str(termindex) + os.linesep)
    indexfile.close()

    # Calculate term frequency (TF), document frequency (DF), and inverse document frequency (IDF)
    tf = {}
    df = {}
    for term in g:
        tf[term] = alltokens.count(term)
        df[term] = sum(1 for doc in alldocs if term in open(dirname + '/' + doc).read().lower().split())

    idf = {term: log(documents / (df[term] + 1)) for term in g}

    # Calculate tf-idf weighting
    tf_idf = {term: tf[term] * idf[term] for term in g}

    # Output postings to disk file
    postingsfile = open(dirname + '/' + 'Postings.dat', 'w')
    for term in g:
        term_id = g.index(term) + 1
        for doc in alldocs:
            doc_id = alldocs.index(doc) + 1
            term_freq = open(dirname + '/' + doc).read().lower().split().count(term)
            doc_freq = df[term]
            tf_idf_weight = tf_idf[term]
            postingsfile.write(f"{term_id},{doc_id},{tf_idf_weight},{term_freq},{doc_freq}{os.linesep}")
    postingsfile.close()

    # Print metrics on corpus
    print(f"Processing Start Time: {t2.tm_hour:02d}:{t2.tm_min:02d}:{t2.tm_sec:02d}")
    print(f"Documents: {documents}")
    print(f"Tokens: {tokens}")
    print(f"Terms: {terms}")
    print(f"Stop words encountered: {stop_words_count}")

    # Creates database
    db_file = open(dirname + '/' + 'inverted_index.db', 'w') 
    for term, data in invert_index.items(): 
        db_file.write(f"{term}: {data}\n") 
    db_file.close()

    t2 = time.localtime()
    print(f"Processing End Time: {t2.tm_hour:02d}:{t2.tm_min:02d}:{t2.tm_sec:02d}")
    print("Index built successfully.")