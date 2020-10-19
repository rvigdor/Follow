from pygraphviz import *
fname = 'test_01'

def graph_url(obj):
    """return a string of dotted concatenated names of all subgraph hirarchy up to but not including the top graph
    only works for named subgraphs by design. removes cluster_ from beginning of names"""
    res = obj.get_name()
    if not res:
        return res
    else:
        res = res.replace('cluster_', "")
        while True:
            obj = obj.subgraph_parent()
            name = obj.get_name()
            if name:
                res += '.' + name.replace('cluster_', "")
            else:
                break
    return res


def mk_sg_name(obj, id, cluster):
    """returns the name for the subgraph, concatenating the obj's url
    with . id and optionally prefixing with cluster_ if cluster"""
    name = graph_url(obj)
    name = f'{name}.{id}' if name else id
    name = 'cluster_' + name if cluster else name
    return name


def add_row(obj, id, n_label, e_label, row_len, cluster=False):
    """constructs a row of elements within a new subgraph within the given obj.
    the row will have row_len nr of nodes, each with n_label,
        connected by edges with e_label. the name of the subgraph will be
        graph_url(obj) + '.' + id. returns row"""
    id = mk_sg_name(obj, id, False)
    row = obj.add_subgraph(id , rank='same')
    for i in range(row_len):
        row.add_node(id + '.' + str(i), label=n_label)
    for i in range(row_len - 1):
        row.add_edge(id + '.' + str(i), id + '.' + str(i + 1), label=e_label)
    return row

def add_row_from_list(obj, id, n_label, e_label, n_list, cluster=False):
    """constructs a row of elements within a new subgraph within the given obj.
    the row will consist of the node labels given in the list, each with n_label,
        connected by edges with e_label. the name of the subgraph will be
        graph_url(obj) + '.' + id. returns row"""
    id = mk_sg_name(obj, id, False)
    row = obj.add_subgraph(id , rank='same')
    for i,lbl in enumerate(n_list):
        row.add_node(f'{id}.{lbl}', label=f'<<B>\'{lbl}\'</B>>')
    for i in range(len(n_list)-1):
        row.add_edge(f'{id}.{n_list[i]}',f'{id}.{n_list[i+1]}', label=e_label)
    return row



def add_seq(obj, id, label, seq_len, first_n_label='SEQ', first_e_label='els', n_label='e',
            e_label='nxt', row_id='seq', cluster=True):
    """construct a sequence within a newly created subgraph in obj: the sequence is a row of nodes with labels n_label,
    connected by edges with label e_label. this first element of this row is attached to a first node
    labeled label with a first edge label first_e_label. the ids of the row elements will be prefixed by row_id .
    if cluster, then the subgraph will be created with a cluster_ prefix (see graphviz). returns seq"""
    cluster_id = mk_sg_name(obj, id, cluster)
    first_n_id = f'{mk_sg_name(obj,id, False)}.{row_id}'
    seq = A.add_subgraph(name=cluster_id, rank='same', label=label)
    seq.add_node(first_n_id, label=first_n_label)
    add_row(seq, row_id, n_label, e_label, seq_len)
    seq.add_edge(first_n_id , f'{first_n_id}.0', label=first_e_label)
    return seq


def add_values(obj, id, label, n_label_list, first_n_label='VALS', first_e_label='vals', e_label='nxt', row_id='vals', cluster=True):
    """construct a sequence within a newly created subgraph in obj: the sequence is a row of nodes with labels in n_label_list,
    connected by edges with label e_label. this first element of this row is attached to a first node
    labeled label with a first edge label first_e_label. the ids of the row elements will be prefixed by row_id .
    if cluster, then the subgraph will be created with a cluster_ prefix (see graphviz). returns seq"""
    cluster_id = mk_sg_name(obj, id, cluster)
    first_n_id = f'{mk_sg_name(obj,id, False)}.{row_id}'
    seq = A.add_subgraph(name=cluster_id, rank='same', label=label)
    seq.add_node(first_n_id, label=first_n_label)
    add_row_from_list(seq, row_id, label, e_label, n_label_list)
    seq.add_edge(first_n_id , f'{first_n_id}.{n_label_list[0]}', label=first_e_label)
    return seq


def add_transform(obj, id, label, row_lens=[],
                    first_n_label='TRNS',
                    first_n_id='trns',
                    row_ids=['in','out'],
                    first_e_labels=['in','out'],
                    n_labels=['i', 'o'],
                    e_labels=['nxt','nxt'],
                    cluster=True):
    """same as add_seq, but constructs a subgraph with two rows for inputs and outputs. returns seq"""
    cluster_id = mk_sg_name(obj, id, cluster)
    first_n_id = f'{mk_sg_name(obj,id, False)}.{first_n_id}'
    seq = A.add_subgraph(name=cluster_id, rank='same', label=label)
    seq.add_node(first_n_id, label=first_n_label)
    for i in range(len(row_lens)):
        # print(i)
        add_row(seq, row_ids[i], n_labels[i], e_labels[i], row_lens[i])
        seq.add_edge(first_n_id , f'{id}.{row_ids[i]}.0', label=first_e_labels[i])
    return seq


class Sequence():
    def __init__(self):
        self.elements = []

    def get_el(self, branch, inx):
        print(f'in sequence, called with branch:{branch} and inx: {inx}')
        return [edge['obj'].get_el(edge['branch'], edge['inx']) for edge in self.elements[inx]]

def reverse_inputs(inputs, outputs, inx):
    """example transform fn for a Transform instance,
    for now, returns the input element as a function
    of inputs outpus and inx"""
    return inputs[::-1][inx]

class Transform():
    def __init__(self, transform_fn):
        self.outputs = []
        self.inputs = []
        self.transform_fn = transform_fn

    def get_el(self, branch, inx):
        print(f'in transform, called with branch:{branch} and inx: {inx}')
        return [edge['obj'].get_el(edge['branch'], edge['inx']) for edge in self.transform_fn(self.inputs, self.outputs, inx)]

class Values():
    def __init__(self, vals):
        self.values = vals

    def get_el(self, branch, inx):
        print(f'in values, called with branch:{branch} and inx: {inx}')
        return self.values[inx]



A = AGraph(directed=True, rankdir='LR', compound=True) # ranksep='0.2', nodesep='1.0'
# A.node_attr["style"] = "filled"
A.node_attr["shape"] = "box"
A.node_attr["style"] = "rounded"
A.edge_attr["fontname"] = "Chilanka"
A.node_attr["fontname"] = "Chilanka"

A.add_node(2, fontsize= '30', label="Main music compiles to\n E-1/2, D-1/8, E-1/8")
A.add_node(1, fontsize= '30',label="A Simple feasibility \ntest of the Follow concept")


# define a seq. this is our 'main', our music
se = Sequence()
# add to graph for visualization
seq1 = add_seq(obj=A, id='seq1', label="The 'Main' music", seq_len=3)
# define another seq. some of notes of se will follow some of the notes in se2
se2 = Sequence()
# add to graph for visualization
seq2 = add_seq(obj=A, id='seq2', label="Phrase which is followed", seq_len=2)
#define some values for durations
r = Values(['1/2', '1/4', '1/8'])
# add to graph for visualization
durations = add_values(obj=A, id='durations', label='DURATIONS', n_label_list=['1/2','1/4','1/8'],e_label='*1/2')
#define some values for pitches
p = Values(['C', 'D', 'E', 'F', 'G', 'A', 'B'])
# add to graph for visualization
scale =    add_values(obj=A, id='scale',label='C Major', n_label_list=['C', 'D', 'E', 'F', 'G', 'A', 'B'])
#instantiate a transformer with the reverse_inputs fn
t = Transform(reverse_inputs)
# add to graph for visualization
tr1 = add_transform(obj=A, id='trans', label='Reverse inputs', row_lens=[3,3])
#for now, a primitive demo, so cruedly add follow edges for element 0. pointing to r.0.0 and p.0.2
se.elements.append([{'obj':r, 'branch': 0, 'inx':0},
               {'obj':p, 'branch': 0, 'inx':2}])
# add to graph for visualization
A.add_edge('seq1.seq.0', 'durations.vals.1/2', label='r', color='red')
A.add_edge('seq1.seq.0', 'scale.vals.E', label='p', color='blue')
#append an element following an element from se2.elements.0
se.elements.append([{'obj':se2, 'branch': 'elements', 'inx':0}])
# add to graph for visualization
A.add_edge('seq1.seq.1', 'seq2.seq.0')
#append an element following an output transform element t.outputs.0
se.elements.append([{'obj':t, 'branch': 'outputs', 'inx': 0}])
# add to graph for visualization
A.add_edge('seq1.seq.2', 'trans.out.0')
#append an element to se2, following r.0.2 and p.0.1
se2.elements.append([{'obj':r, 'branch': 0, 'inx':2},
               {'obj':p, 'branch': 0, 'inx':1}])
# add to graph for visualization
A.add_edge('seq2.seq.0', 'durations.vals.1/8', label='r', color='red')
A.add_edge('seq2.seq.0', 'scale.vals.D', label='p', color='blue')
#append input element in t following r.0.0 and p.0.0
t.inputs.append([{'obj':r, 'branch': 0, 'inx':0},
               {'obj':p, 'branch': 0, 'inx':0}])
# add to graph for visualization
A.add_edge('trans.in.0', 'durations.vals.1/2', label='r', color='red')
A.add_edge('trans.in.0', 'scale.vals.C', label='p', color='blue')
#append input element in t following r.0.1 and p.0.1
t.inputs.append([{'obj':r, 'branch': 0, 'inx':1},
               {'obj':p, 'branch': 0, 'inx':1}])
# add to graph for visualization
A.add_edge('trans.in.1', 'durations.vals.1/4', label='r', color='red')
A.add_edge('trans.in.1', 'scale.vals.D', label='p', color='blue')
#append input element in t following r.0.2 and p.0.2
t.inputs.append([{'obj':r, 'branch': 0, 'inx':2},
               {'obj':p, 'branch': 0, 'inx':2}])
# add to graph for visualization
A.add_edge('trans.in.2', 'durations.vals.1/8', label='r', color='red')
A.add_edge('trans.in.2', 'scale.vals.E', label='p', color='blue')


print(A.string())  # print to screen
A.write(f"{fname}.dot")  # write to simple.dot
A.draw(f"{fname}.png", prog="dot")  # draw to png using dot

#print our resolved music. some notes follow values directly, some through a second phrase(se2)
#and some through transform t
for i in range(3):
    print(se.get_el(0,i))