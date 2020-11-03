
from cdlib import algorithms, viz
import networkx as nx
from gesetz import Gesetz
from networkx.algorithms.hierarchy import flow_hierarchy
from networkx.algorithms.components import strongly_connected_components, weakly_connected_components
from networkx.algorithms.dag import lexicographical_topological_sort
import datetime
import json
import heapq
import unicodedata





class Graph:
    bigDiMul = None
    pagerank = None
    louvain = None
    topic = None
    hand_picked = {
        "Erfurt":{
            "relevant":["ÄArbVtrG", "ArbGG","ArbZG","AÜG","BetrVG","BUrlG","DrittelbG","EntgTranspG","FPfZG","KSchG","MiLoG","MitbestG","MontanMitbestG","NachwG","PflegeZG","SprAuG","TVG","EFZG","WZVG"],
            "auszuege":["GG","AEntG","AGG","AktG","ArbPlSchG","ArbSchG","BBiG","BDSG","BEEG","BetrAVG","BGB","GenDG","GewO","HAG","HGB","InsO","JArbSchG","MuSchG","TzBfG","UmwG","ATG"]
        },
        "Beck":{
            "relevant":["AEntG", "AGG","ArbZG","AÜG","BUrlG","EntgTranspG","FPfZG","KSchG","MiLoG","PflegeZG","TVG","TzBfG","ATG","EFZG"],
            "auszuege":["ArbGG","BBiG","BEEG","BetrAVG","BetrVG","BGB","BGBEG","GewO","GG","HGB","InsO","MuSchG","VO","MiArbG"]
        },
        "Umwelt":{
            "relevant":["BGBEG", "KrWG","BImSchG","BBodSchG","UBAG","USchadG","UmwRG","WHG","BNatSchG","TEHG","UVPG","OstSUmwSchÜbkG","LMeerSchÜbkG"]
        },
        "StrafR nomos":{
            "relevant":["StGB", "EGStGB","SubvG","UWG","UrhG","VStGB","WpHG","StVG","AufenthG","AsylG","BtMG","WStG","WaffG","JuSchG","VersammlG","G 10","OWiG","NetzDG","GVG","EGGVG","StPO","StPOEG","JGG","IStGHG","IRG","StVollzG","BZRG","StrEG","OEG","JVEG","RVG","GG"]
        },
        "UmwR beck":{
            "relevant":["UBAG", "DBUStiftG","UStatG","UVPG","UIG","UAG","USchadG","BfNatSchG","BNatSchG","TierSchG","BBodSchG","WHG","AbwAG","WRMG","KrWG","ElektroG","BattG","VerpackG","BImSchG","BzBlG","TEHG","SchlärmschG","KSG","BEHG","G BAStrlSchG","BfkEG","AtG","EnEG","StromStG","EVPG","EEWärmeG","EmoG","CsgG","ChemG","GenTG","UmweltHG","UmwRG"]
        },
        "GesR beck":{
            "relevant":[u"AktG", u"AktGEG",u"GmbHG",u"EGGmbHG",u"GenG",u"HGBEG",u"PublG",u"PartGG",u"SEAG",u"EWIVAG",u"WpHG",u"WpÜG",u"UmwG",u"MitbestG",u"MontanMitbestG",u"MontanMitbestGErgG",u"DrittelbG",u"MgVG",u"SEBG",u"SpruchG",u"COVInsAG",u"GesRuaCOVBekG"]
        },
        "WaffR Beck":{
            "relevant":["WaffG", "NWRG","BeschG","SprengG"]
        },
        "BankR beck":{
            "relevant":["BBankG", "FinDAG","KWG","FKAG","ZAG","AnlEntG","EinSiG","ZKG","GwG","PfandBG","BauSparkG","FMStFG","FMStBG","KredReorgG","RStruktFG","SAG","ScheckG","WG"]
        },
        "ArbText beck":{
            "relevant":["AGG", "AEntG","ArbnErfG","AÜG","ArbGG","AnlEntG","ArbSchG","ArbZG","AsylbLG","AAG","ÄArbVtrG","BBiG","BetrVG","BEEG","BUrlG","DrittelbG","EntgTranspG","EBRG", "FPfZG", "HAG", "KSchG", "LadSchlG", "MiLoG", "MitbestG", "MontanMitbestGErgG", "MontanMitbestG", "MuSchG", "NachwG", "PflegeZG", "SprAuG", "TVG", "TzBfG", "WissZeitVG", "ZPO"]
        }
    }

    @staticmethod
    def get_subgraph(nodes):
        return Graph.bigDiMul.subgraph(nodes).copy()

    def __init__(self,hand_picked,hand_picked_auszuege=[]):
        not_found = []
        found_rel = []
        found_aus = []
        for pick_raw in hand_picked:
            pick = unicodedata.normalize("NFKC", pick_raw)
            found = False
            for node in Gesetz.collected_laws.keys():
                if pick == node:
                    found = True
                    found_rel.append(node)
            if not found:
                not_found.append(node)

        for pick_raw in hand_picked_auszuege:
            pick = unicodedata.normalize("NFKC", pick_raw)
            found = False
            for node in Gesetz.collected_laws.keys():
                if node==pick:
                    found = True
                    found_aus.append(node)
            if not found:
                not_found.append(node)

        print("not found: " + str(not_found))

        self.G_all = Graph.get_subgraph(found_rel+found_aus)
        self.G_rel = Graph.get_subgraph(found_rel)
        self.build_layers()
        self.core = None
        for component in strongly_connected_components(self.G_rel):
            if self.core == None or len(self.core)<len(component):
                self.core = component

    def get_auszug(self,node):
        return 0 if node not in self.G_rel else 1

    def get_core(self,node):
        return 1 if node in self.core else 0
    
    def get_topic(self,node):
        return Graph.topic[node]

    def get_louvain(self,node):
        return Graph.louvain[node]

    def get_pagerank(self,node):
        return Graph.pagerank[node]

    def get_flow(self):
        return nx.flow_hierarchy(self.G_rel)

    def get_closure(self):
        inner = 0
        total = 0
        for node in self.G_rel:
            for nbr in self.bigDiMul.neighbors(node):
                total = total +1
                if nbr in self.G_rel:
                    inner = inner +1

        return inner/total

    def get_layer(self,node):
        return self.layers[node]

    def get_picked(self,node):
        for name in Graph.hand_picked:
            if node in Graph.hand_picked[name]["relevant"]:
                return name
        return "None"

    def build_layers(self):
        def build_metagraph(components,graph):
            G = nx.MultiDiGraph()
            for key in set(components.values()):
                G.add_node(key)
            for (s,t,n) in graph.edges:
                #if n==0:
                    #print(s+"->"+t)
                if components[s] != components[t]:
                    G.add_edge(components[s],components[t])
            return G

        def get_topo_sort(graph,sort_key):
            comp = strongly_connected_components(graph)
            components = {}
            i = 0
            keys = {}
            for component in strongly_connected_components(graph):
                i = i+1
                for node in component:
                    components[node] = i
                if i not in keys or keys[i]<sort_key(node):
                    keys[i]=sort_key(node)

            meta_graph = build_metagraph(components,graph)
            to_return = []

            def max_key(compared_meta_node):
                to_return = keys[compared_meta_node]
                #print("returned: "+str(to_return))
                return to_return
            #print(keys)
            connected_components = list(reversed(list(lexicographical_topological_sort(meta_graph,max_key))))

            for index in range(len(connected_components)):
                meta_node = connected_components[index]

                to_return.append([])
                for node in components:
                    if components[node] == meta_node:
                        to_return[-1].append(node)
            return to_return

        def sort_digraph(graph,sort_key):
            to_sort = []
            for comp in weakly_connected_components(graph):
                to_sort.append((len(comp),comp))
            to_sort.sort(reverse=True)
            to_return = []
            for comp in to_sort:
                #print(comp)
                sub_graph = Graph.get_subgraph(comp[1])
                to_return.append(get_topo_sort(sub_graph,sort_key))
            return to_return

        def sort_key(node):
            return datetime.datetime.today() - Gesetz.collected_laws[node].date
        sorted_di = sort_digraph(self.G_rel,sort_key)

        self.layers = {}
        for weak_component in sorted_di:
            for index in range(len(weak_component)):
                for node in weak_component[-1-index]:
                    self.layers[node] = index+3

        for node in self.G_all:
            if node not in self.G_rel:
                self.layers[node] = 0


    def add_to_network(self,network,theshhold=0):
        def addnode(node,nodes):
            nodes[node]={}
            nodes[node]["Topic"] = self.get_topic(node)
            nodes[node]["Auszug"] = self.get_auszug(node)
            nodes[node]["Core"] = self.get_core(node)
            nodes[node]["TopoSort"]= self.get_layer(node)
            nodes[node]["Louvain"]= self.get_louvain(node)
            nodes[node]["PageRank"]= self.get_pagerank(node)
            nodes[node]["Rechtsgebiet"] = self.get_picked(node)
            nodes[node]["ist_in_sammlung"] = True if self.get_picked(node) != None else False

        nodes = {}
        if theshhold == 0:
            for node in self.G_all:
                addnode(node,nodes)

        edges = []
        for (s,t,n) in self.G_all.edges:
            if(n>=theshhold):
                if s not in nodes:
                    addnode(s,nodes)
                if t not in nodes:
                    addnode(t,nodes)

                edges.append([s,t])


        network.add_layer(
            nodes=nodes,
            adjacency=edges
        )

    @staticmethod
    def set_big(collected_laws):
        Graph.bigDiMul = nx.MultiDiGraph()
        for law in Gesetz.collected_laws.values():
            Graph.bigDiMul.add_node(law.name_short)
        for law in Gesetz.collected_laws.values():
            for link in law.links:
                if link.target in Graph.bigDiMul and law.name_short in Graph.bigDiMul:
                    if link.target == None:
                        print("Found null node and link!")
                    else:
                        Graph.bigDiMul.add_edge(law.name_short,link.target)
        
        Graph.pagerank = nx.pagerank(nx.DiGraph(Graph.bigDiMul))

        center = None
        for component in weakly_connected_components(Graph.bigDiMul):
            if center == None or len(center)<len(component):
                center = component

        bigMul = nx.MultiGraph()
        for (s,t) in Graph.bigDiMul.edges():
            if s in center and t in center:
                bigMul.add_edge(s,t)

        coms1 = algorithms.louvain(bigMul,resolution=0.9)
        Graph.louvain = {}
        for node in Graph.bigDiMul.nodes:
            Graph.louvain[node]=0
        index = 1
        for com in coms1.communities:
            index = index+1
            for node in com:
                Graph.louvain[node] = index

        Graph.topic = {}
        for node in Graph.bigDiMul:
            Graph.topic[node] = collected_laws[node].get_topic()
        print(set(Graph.louvain.values()))





    @staticmethod
    def build_handpicked(name):
        if "auszuege" in Graph.hand_picked[name]:
            return Graph(Graph.hand_picked[name]["relevant"],Graph.hand_picked[name]["auszuege"])
        else:
            return Graph(Graph.hand_picked[name]["relevant"])

    @staticmethod
    def get_handpicked_laws(name):
        return [unicodedata.normalize("NFKC", law) for law in Graph.hand_picked[name]["relevant"] if unicodedata.normalize("NFKC", law) in Graph.bigDiMul]

    @staticmethod
    def get_topic_laws(name):
        return [law for law in Graph.bigDiMul if Graph.topic[law]==name]

    @staticmethod
    def build_topics(topics):
        relevant = []
        for law in Graph.bigDiMul:
            if Graph.topic[law] in topics:
                relevant.append(law)
        return Graph(relevant)

    @staticmethod
    def build_louvain(array):
        relevant = []
        for law in Graph.bigDiMul:
            if Graph.louvain[law] in array:
                relevant.append(law)

        #to_return = nx.Graph()
        #for node in relevant:
        #    to_return.append(node)
        #for (s,t) in Graph.bigDiMul.edges():
        #    if Graph.louvain[s] == Graph.louvain[t]:
        #        to_return.add_edge(s,t)

        return Graph(relevant)

    @staticmethod
    def build_all():
        return Graph([node for node in Graph.bigDiMul.node])

    def filter_oldest(self,amount):
        nodes = []
        for node in self.G_all:
            heapq.heappush(nodes,(datetime.datetime.today() - Gesetz.collected_laws[node].date,node))
            if len(nodes) > amount:
                heapq.heappop(nodes)
        return Graph([node[1] for node in nodes])