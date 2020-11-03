import re
import datetime
from nltk.stem.cistem import Cistem
from nltk.tokenize import word_tokenize 
from nltk.corpus import stopwords

class Gesetz:
    """This class represents parsed laws"""
    collected_laws = {}
    topic_names = {}


    def __init__(self,text:str,filename:str):
        #print(str(Gesetz.aliases))
        self.name_file = filename
        self.name_full = None
        self.links = []
        self.aliases = []
        self.stems=[]
        self.topics = None
        if self.is_law():
            self.parse(text)
            if self.is_law():
                Gesetz.collected_laws[self.name_short] = self

    def set_topics(self,topics):
        sorted_topics = sorted(((d,n+1) for n, d in topics),reverse=True)
        self.topics = [(Gesetz.translate_topic(n),p) for (p,n) in sorted_topics]

    def get_topic(self):
        if len(self.topics)>0:
            return self.topics[0][0]
        else:
            return None


    def parse(self,text:str):

        def remove_prefix(to_shorten:str) -> str:
            if to_shorten[:134] == "Ein Service des Bundesministeriums der Justiz und für Verbraucherschutz\nsowie des Bundesamts für Justiz ‒ www.gesetze-im-internet.de\n\n":
                to_return = re.sub('- Seite [\d+] von [\d+] -', '', to_shorten[134:])
                to_return = to_return.replace("Ein Service des Bundesministeriums der Justiz und für Verbraucherschutz\nsowie des Bundesamts für Justiz ‒ www.gesetze-im-internet.de","")
                return to_return        
            else:
                print("Not added file "+self.name_file+" because I don't know how to trim the prefix:")
                print(to_shorten[:134])
                return None

        def is_same_short(name1:str,name2:str) -> bool:
            return name1.replace("-","") == name2.replace("-","")
        
        text =  remove_prefix(text)

        if text == None:
            return None

        match_date = re.search("\n(.*)\nAusfertigungsdatum: (\d+\.\d+\.\d+)",text)
        if not match_date:
            print("No date found in "+self.name_file + "!")

        self.name_short = match_date.group(1)
        if self.name_file[:-4]!=self.name_short:
            #print("Differing filename '"+self.name_file[:-4]+"' and short_name '"+self.name_short+"'")
            pass
        self.aliases = []
        self.stems = []

        date = datetime.datetime.strptime(match_date.group(2),'%d.%m.%Y')
        self.date = date
        before_date = text[0:match_date.span()[0]]
        before_date = before_date.replace("\n"," ")
        bracket = re.search("\(.*\)",before_date)
        if bracket:
            self.name_full = before_date[:bracket.span()[0]-1]

            all_brackets = re.findall('\((.*?)\)', before_date) # Search for all brackets (and store their content)
            bracket_content = all_brackets[-1] # Get the last one

            bracket_minus = re.search(" - ",bracket_content)
            alias = None
            if is_same_short(bracket_content, self.name_short) :
                pass
            elif bracket_minus:
                parts = bracket_content.split(" - ")
                before_minus = bracket_content[:-(len(parts[-1])+3)]
                if is_same_short(parts[-1],self.name_short):
                    alias = before_minus
                else:
                    pass
                    #print(self.name_short+";" + before_minus + ";" + bracket_content)

            elif not " " in bracket_content:
                if len(bracket_content)>6 and bracket_content[-6:] == "gesetz":
                    alias = bracket_content
                else:
                    pass
                    #print("No space, not understood: " +self.name_short + ";" +before_date)
            elif bracket_content.lower()[-6:] == "gesetz":
                alias = bracket_content
                #print(self.name_short +";"+ before_date)
            else:
                parts = bracket_content.split(" ")
                if is_same_short(parts[-1], self.name_short) and parts[-2][-6:].lower() == "gesetz":
                    alias = bracket_content[:-(len(self.name_short)+1)]
                elif parts[0][-6:].lower()=="gesetz":
                    alias = bracket_content
                    #print(self.name_short +";"+ before_date)
                else:
                    pass
                    #print(self.name_short +": "+ before_date)

            if alias != None and alias not in self.aliases:
                self.aliases.append(alias)
                #print("Added alias "+self.name_short+": "+Gesetz.aliases[self.name_short][-1])

        else:
            self.name_full = before_date

        if self.name_full.strip() not in self.aliases:
            self.aliases.append(self.name_full.strip())

        stemmer = Cistem()

        for alias in self.aliases:
            self.stems.append([stemmer.stem(token) for token in word_tokenize(alias, language='german') if token not in stopwords.words('german')])
        #print(self.name_short+": "+str(self.stem))

        match_vollzitat = re.search("Vollzitat:",text)
        self.content = text[match_vollzitat.span()[1]+1:]

    def is_law(self) -> bool:
        last_letter = self.name_file[-5]
        file_name = self.name_file[:-4]

        if last_letter not in ["G","B","O"]:
            #if last_letter in ["0","1","2","3","4","5","6","7","8","9"]:
            #    print("digit: "+file_name)
            return False
        
        #if self.name_full is not None and ("Abk" in file_name):
        #    print("Found Abkommen("+self.name_short+"): "+self.name_full)

        if  ("_DV-" in file_name) or ("DV"==file_name[0:2]):
            return False

        if file_name.endswith("VO") or file_name.endswith("VollzO") or file_name.endswith("BO") or file_name.endswith("AnO"):
            return False

        keine_gesetze = []
        #keine_gesetze = ["BKostV-MPG","SStellV-VVG","GGVSEB","MORVorschr","RadarPatEVB","SachBezV","ZOVersDTAG","ndigkeits-DB","AuslfVtr","RHiVtr","SVVtr"]
        for kein_gesetz in keine_gesetze:
            if kein_gesetz in file_name:
                #print("Special rule found: "+kein_gesetz)
                return False

        if self.name_full is not None and "verordnung" in self.name_full.lower() and not "gesetz" in self.name_full.lower():
            #print("Found verordnung("+self.name_short+"): "+self.name_full)
            return False

        if self.name_full is not None and (self.name_full.lower().startswith("verordnung") or self.aliases[0].lower().startswith("verordnung")):
            pass
            print("Verordnung("+self.name_short+"): "+self.name_full)
            return False

        return True

    @staticmethod
    def translate_topic(topic):
        if topic in Gesetz.topic_names:
            return Gesetz.topic_names[topic][1]
        else:
            return str(topic)

    @staticmethod
    def get_topic_count():
        topic_count = {}
        for law in Gesetz.collected_laws.values():
            topic = law.get_topic()
            #print(topic)
            if topic not in topic_count:
                topic_count[topic] = 0
            topic_count[topic] = topic_count[topic] + 1
        return topic_count


    @staticmethod
    def cut_off_small_topics(lower_threshold,upper_threshold):
        topic_count = Gesetz.get_topic_count()
        to_keep =[]
        to_discard = []
        for topic in topic_count:
            if topic_count[topic]>=lower_threshold and topic_count[topic]<=upper_threshold:
                to_keep.append(topic)
            else:
                to_discard.append(topic)

        for law in Gesetz.collected_laws:
            law_topic_to_keep = []
            for (top,prob) in Gesetz.collected_laws[law].topics:
                if top in to_keep:
                    law_topic_to_keep.append((top,prob))
            summ = sum([p for (t,p) in law_topic_to_keep])
            if summ != 0:
                factor = 1/summ
            else:
                factor = 1
            law_topic_scaled = [(t,p*factor) for (t,p) in law_topic_to_keep]
            Gesetz.collected_laws[law].topics = law_topic_scaled
        print("discarded: "+str(to_discard))
        print("kept: "+str(to_keep))


    @staticmethod
    def populate_genitiv():
        for short in Gesetz.collected_laws:
            for index in range(len(Gesetz.collected_laws[short].aliases)):
                alias = Gesetz.collected_laws[short].aliases[index]
                if len(alias) <6:
                    continue
                
                gesetz = re.search("gesetz ",alias.lower())
                buch = re.search("buch ",alias.lower())
                candidate = None
                if gesetz:
                    candidate = alias[:gesetz.span()[0]+1]+"esetzes "+alias[gesetz.span()[1]:]

                elif alias.lower()[-6:] =="gesetz":
                    candidate = alias+"es"

                elif buch:
                    candidate = alias[:buch.span()[0]+1]+"uches "+alias[buch.span()[1]:]

                elif alias.lower()[-4:] =="buch":
                    candidate = alias+"es"
                
                if candidate not in Gesetz.collected_laws[short].aliases and "gesetzes" not in alias.lower() and "buches" not in alias.lower():
                    if candidate is None:
                        print("No Genitiv found ("+short+"): "+alias)
                    else: 
                        Gesetz.collected_laws[short].aliases.append(candidate)

    def print(self):
        print(self.name_short+str(self.date.date())+"]"+": "+self.name_full)

        if len(self.content)>500:
            print("Content: " + self.content[:500]+"...")
        else:
            print("Content: " + self.content[:500]+"...")

    def __str__(self):
        return self.name_short


    def find_outward_links(self,stemming=True,verbose=False):
        stemmer = Cistem()
        def stem(text):
            return  [stemmer.stem(token) for token in word_tokenize(text, language='german')]

        content = self.content
        re.DOTALL
        self.links = []
        while True:
            paragraph = re.search("([\s\S]{0,5})([\s\S])§([^§]{0,100}[^§ ]*)",content)
            if paragraph:
                found_string = paragraph.group(0)
                behind_paragraph = paragraph.group(3).replace("\n","[n]")
                if paragraph.group(2) == "\n":
                    #print("newline: "+found_string[1:])
                    pass
                else:
                    lnk = Link()
                    lnk.fulltext = "$"+behind_paragraph

                    #print("behind §: "+behind_paragraph)
                    for short_other in Gesetz.collected_laws:
                        if stemming:
                            for stem_other in Gesetz.collected_laws[short_other].stems:
                                behind_without_umlaute = behind_paragraph.lower().replace("ä","a").replace("ö","o").replace("ü","u").replace("ß","ss")
                                if not any([word not in behind_without_umlaute for word in stem_other])  and short_other!=self.name_short:
                                    stemmed = stem(behind_paragraph.replace("[n]"," "))
                                    if not any([word not in stemmed for word in stem_other]):
                                        #print("Found link to "+short_other+": "+behind_paragraph)
                                        if lnk.target == None:
                                            lnk.target = short_other
                                            lnk.hit = stem_other
                                            if verbose and not any( [alias_other.lower() in behind_paragraph.lower().replace("[n]"," ") for alias_other in Gesetz.collected_laws[short_other].aliases]):
                                                print("\n"+short_other+" found new link by stemming : "+behind_paragraph)
                                                print(Gesetz.collected_laws[short_other].aliases)
                                        else:
                                            keep_other = None
                                            for word in stemmed:
                                                if word in lnk.hit and (word not in stem_other):
                                                    keep_other = True
                                                    break
                                                elif word in stem_other:
                                                    keep_other = False
                                                    break
                                            if keep_other == None:
                                                keep_other = len(lnk.hit) <= len(stem_other)
                                                
                                            if not keep_other:
                                                if verbose:
                                                    print("Replaced hit "+lnk.target+" by "+short_other+" in "+behind_paragraph)
                                                lnk.target = short_other
                                                lnk.hit = stem_other
                                            elif verbose:
                                                print("Kept hit "+lnk.target+" vs. "+short_other+" in: "+behind_paragraph)

                        else:    
                            for alias_other in Gesetz.collected_laws[short_other].aliases:
                                if alias_other.lower() in behind_paragraph.lower().replace("[n]"," ") and short_other!=self.name_short:
                                    #print("Found link to "+short_other+": "+behind_paragraph)
                                    lnk.target = short_other
                                    lnk.hit = alias_other
                                    #print(lnk.fulltext)
                                    stemmed = stem(behind_paragraph.replace("[n]"," "))
                                    if not any([not any([word not in stemmed for word in stem]) for stem in Gesetz.collected_laws[short_other].stems]):
                                        print("\n "+short_other+" discarded by stemming: "+behind_paragraph+"\n"+str(lnk.hit)+" - "+str(Gesetz.collected_laws[short_other].stems)+" not in "+str(stemmed))



                    if lnk.target == None:
                        match_gesetz = re.search("([^ ]*.gesetz(|es)) ",behind_paragraph.lower())
                        if  match_gesetz:
                            lnk.hit = match_gesetz.group(1)
                            #print("link to "+match_gesetz.group(1)+": "+found_string)
                        else: 
                            pass
                            #print("nothing: "+found_string)
                    if lnk.hit != None:
                        #print("something: "+lnk.fulltext)
                        self.links.append(lnk)
                    else:
                        pass
                        
                # Cut of until paragraph symbol
                content = content[paragraph.span()[0]+len(paragraph.group(1))+1:]
            else:
                break



    def print_links(self):
        for link in self.links:
            string = ""
            if link.target == None:
                string = "----------"
            else:
                string = link.target.ljust(10)

            string = string + " - " + link.fulltext
            print(string)
                

class Link:
    """This class represents a link from one law to an other law."""

    def __init__(self):
        #print(str(Gesetz.aliases))
        self.target = None
        self.hit = None
        self.fulltext = None



def progressBar(iterable, prefix = 'Progress', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function
    def printProgressBar (iteration,item):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        if item is not None:
            print(f'\r{iteration}/{total} |{bar}| {percent}% ({item})', end = printEnd)
    # Initial Call
    printProgressBar(0,None)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1,item)
    # Print New Line on Complete
    print()