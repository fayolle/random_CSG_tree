import random
import sys
import warnings
import argparse


#------------------------------------------------------------------------------
# Some parameter controlling the simulation. 
# Global for now, will be moved later.

# default value for the max depth for each tree creature:
MAX_DEPTH = 10

# default value for the number generated random trees:
POP_SIZE = 10


# These variables keep the list of available nodes and operations.
# They are set at the beginning of the program and only read by the functions
# below.
g_list_terminalnodes = []
g_list_operations = []


#------------------------------------------------------------------------------


class Primitive(object):
    pass


class PlanePrimitive(Primitive):
    def __init__(self, parameters):
        # parameters: normalx normaly normalz dist
        self.normal_vec = (parameters[0], parameters[1], parameters[2])
        self.dist = parameters[3]

    def identifier(self):
        return 'plane'


class SpherePrimitive(Primitive):
    def __init__(self, parameters):
        # parameters: centerx centery centerz radius
        self.center = (parameters[0], parameters[1], parameters[2])
        self.radius = parameters[3]

    def identifier(self):
        return 'sphere'


class CylinderPrimitive(Primitive):
    def __init__(self, parameters):
        # arguments: 
        # axis_dirx axis_diry axis_dirz axis_posx axis_posy axis_posz radius
        self.axis_dir = (parameters[0], parameters[1], parameters[2])
        self.axis_pos = (parameters[3], parameters[4], parameters[5])
        self.radius = parameters[6]

    def identifier(self):
        return 'cylinder'


class TorusPrimitive(Primitive):
    def __init__(self, parameters):
        # parameters: 
        # normalx normaly normalz centerx centery centerz rminor rmajor
        self.normal_vec = (parameters[0], parameters[1], parameters[2])
        self.center = (parameters[3], parameters[4], parameters[5])
        self.rminor = parameters[6]
        self.rmajor = parameters[7]

    def identifier(self):
        return 'torus'

        
class ConePrimitive(Primitive):
    def __init__(self, parameters):
        # parameters: 
        # axis_dirx axis_diry axis_dirz centerx centery centerz angle
        self.axis_dir = (parameters[0], parameters[1], parameters[2])
        self.center = (parameters[3], parameters[4], parameters[5])
        self.angle = parameters[6]

    def identifier(self):
        return 'cone'


class EllipsoidPrimitive(Primitive):
    def __init__(self, parameters):
        assert(len(parameters) == 9)
        self.c = (parameters[0], parameters[1], parameters[2])
        self.r = (parameters[3], parameters[4], parameters[5])
        self.theta, self.phi, self.psi = (parameters[6], parameters[7], parameters[8])

    def identifier(self):
        return 'ellipsoid'


def create_primitive_instance(name, parameters):
    ''' 
    Create an instance of the appropriate primitive based on the primitive
    name.
    '''
    lcname = name.lower()
    if lcname == 'plane':
        return PlanePrimitive(parameters)
    if lcname == 'sphere':
        return SpherePrimitive(parameters)
    if lcname == 'cylinder':
        return CylinderPrimitive(parameters)
    if lcname == 'torus':
        return TorusPrimitive(parameters)
    if lcname == 'cone':
        return ConePrimitive(parameters)
    if lcname == 'ellipsoid':
        return EllipsoidPrimitive(parameters)
    raise Exception('Unknown primitive')


#----------------------------------------------------------------------------


# Creature representation.
# The representation of the trees corresponding to the programs
# being evolved.

class fwrapper(object):
    '''
    A wrapper for the functions that will be used on function 
    nodes (internal nodes). Its member variables are the name 
    of the function, and the number of parameters it takes.
    '''
    def __init__(self, childcount, name):
        self.childcount = childcount
        self.name = name


class node(object):
    '''
    The class for function nodes (nodes with children). This is 
    initialized with an fwrapper. When evaluate is called, it 
    evaluates the child nodes and then applies the function
    to their results.
    '''
    def __init__(self, fw, children):
        self.name = fw.name
        self.children = children

    def display(self, indent=0):
        print (' ' * indent) + self.name
        for c in self.children:
            c.display(indent+1)

    def to_string(self):
        str_to_display = self.name + '['
        num_children = len(self.children)
        for i in range(num_children-1):
            str_to_display = str_to_display + self.children[i].to_string() + ','

        last_child = self.children[num_children-1]
        str_to_display = str_to_display + last_child.to_string()
        str_to_display = str_to_display + ']'
        return str_to_display

    def compute_number_nodes(self):
        ''' Compute the number of nodes (internal nodes and leaves) for 
        the tree.
        '''
        number_nodes = 0
        for c in self.children:
            number_nodes = number_nodes + c.compute_number_nodes()
        return 1 + number_nodes

    def max_depth(self):
        '''
        Returns the depth of the deepest branch of the tree
        '''
        max_depth_children = 0
        for c in self.children:
            max_depth_children = max(max_depth_children, c.max_depth())
        return 1 + max_depth_children


class terminalnode(object):
    '''
    Terminals are leaves. They serve as a wrapper to a function 
    to be evaluated at a point coordinate and return the corresponding 
    value.
    This class serves as a wrapper to the fitted primitives.
    TODO: rename, e.g. primitive?
    '''
    def __init__(self, name):
        self.name = name

    def display(self, indent=0):
        print ('%s%s' % (' '*indent, self.name))

    def to_string(self):
        str_to_display = self.name
        return str_to_display

    def compute_number_nodes(self):
        return 1

    def max_depth(self):
        '''
        Returns the depth of the deepest branch of the tree
        '''
        return 1


#------------------------------------------------------------------------


def makerandomtree(maxdepth=4, opr=0.7):
    '''
    Create a random program.
    Return a new tree.
    Args:
        Is it needed anymore??
        maxdepth: maximum depth for the random tree
        opr: probability to draw an operation
    '''
    if random.random() < opr and maxdepth > 0:
        f = random.choice(g_list_operations)
        children = [makerandomtree(maxdepth-1, opr) for i in range(f.childcount)]
        return node(f, children)
    else:
        leaf = random.choice(g_list_terminalnodes)
        return leaf


#------------------------------------------------------------------------


def create_list_operations():
    unionw = fwrapper(2, 'union')
    intersectionw = fwrapper(2, 'intersection')
    negationw = fwrapper(1, 'negation')
    subtractionw = fwrapper(2, 'subtraction')

    list_operations = [unionw, intersectionw, negationw, subtractionw]
    return list_operations


def create_list_terminalnodes(list_primitives):
    ''' Create a list of terminal nodes from a list of primitive shapes.'''

    list_terminalnodes = []
    count = 0
    for i in range(len(list_primitives)):
        name = list_primitives[i].identifier() + str(count)
        tn = terminalnode(name)
        list_terminalnodes.append(tn)
        count = count + 1

    return list_terminalnodes


#------------------------------------------------------------------------------


def display(population):
    ''' Display each creature of a given population by printing its string
    representation.
    '''
    print('Size of the population: ')
    print(len(population))
    for creature in population:
        print(creature.to_string())
        print('-'*80)


def save_population_to_file(population, file_name='temp_population.txt'):
    '''
    Save the current population in a file for later inspection.
    '''
    with open(file_name, 'w') as f:
        for creature in population:
            f.write(creature.to_string())
            f.write('\n')


def read_operations(file_name):
    '''
    Load the list operations that can be used as internal nodes
    to the evolved trees.
    
    The returned object will have to be passed 
    to makerandomtree() via evolve().

    Args:
        file_name: name of the file with the operations to be used
    '''

    # list of available operations
    available_operations = ['union','intersection','subtraction','negation']
    
    # currently the symbol 'operations_list' is already used globally
    op_list = []
    op_name_list = []

    with open(file_name) as f:
        for line in f:
            line = line.strip()
            # each line should contains an operation name
            if (len(line) == 0):
                continue

            op_name = line.split()[0]
            if not(op_name in available_operations):
                print('Unknown operation')
                continue
            op_name_list.append(op_name)

    # remove duplicates
    op_name_set = set(op_name_list)
    op_name_list = list(op_name_set)

    # create all the wrappers
    # note: currently the names unionw, intersectionw, negationw and 
    # subtractionw are already used
    union_w = fwrapper(2, 'union')
    intersection_w = fwrapper(2, 'intersection')
    negation_w = fwrapper(1, 'negation')
    subtraction_w = fwrapper(2, 'subtraction')

    # map operation names to operation wrappers
    operations_map = {'union': union_w, 'intersection': intersection_w, 'negation': negation_w, 'subtraction': subtraction_w}

    for op_name in op_name_list:
        op_list.append(operations_map[op_name])

    return op_list


def read_fit(fit_filename):
    '''
    Load the list of primitives with their parameters that can be 
    used as leaves for the trees.
    
    The returned list will be used by makerandomtree().
    
    Args:
        file_name: name of the .fit file with the primitives information
    '''

    f = open(fit_filename)

    list_primitives = []

    for line in f:
        elements = line.strip().split()
        if len(elements)==0:
            # empty line
            continue
        # elements will look like:
        # primitive_name parameter_1 parameter_2 ... parameter_n
        primitive_name = elements[0]
        parameters = []
        for i in range(1, len(elements)):
            parameters.append(float(elements[i]))

        list_primitives.append(
            create_primitive_instance(primitive_name, parameters))

    f.close()
    return list_primitives


def save_creature_to_file(creature, filename):
    f = open(filename, "w")
    f.write(creature.to_string())
    f.close()


def save_primitives_list_to_file(tnodes, filename):
    '''
    Save the list of primitives names in a file. Names are separated by a comma.
    '''
    f = open(filename, "w")
    num_prim = len(tnodes)
    for i in range(num_prim-1):
        f.write(tnodes[i].name)
        f.write(',')

    f.write(tnodes[num_prim-1].name)
    f.write('\n')
    
    f.close()


#------------------------------------------------------------------------


def main(fit_file, trees_file="expressions.txt", 
         primitives_file="list_primitives.txt",
         popsize=POP_SIZE, max_depth=MAX_DEPTH):
    global g_list_terminalnodes
    global g_list_operations
    list_primitives = read_fit(fit_file)
    g_list_terminalnodes = create_list_terminalnodes(list_primitives)
    g_list_operations = create_list_operations()

    population = [makerandomtree(maxdepth=max_depth, opr=0.7) for _ in range(popsize)]

    save_population_to_file(population, trees_file)
    save_primitives_list_to_file(g_list_terminalnodes, primitives_file)


# ----------------------------------------------------------------------


def usage(progname):
    print('Usage:')
    print(progname + ' primitives.fit \n')
    print(progname + ' primitives.fit random_creatures.txt primitives.txt\n')


# Main:
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # necessary
    parser.add_argument("fit_in", help="input file containing a list of primitives with fitted parameters")
    
    # optional
    parser.add_argument(
        "--trees_out", 
        help="filename where random trees are saved; Default: expressions.txt")
    parser.add_argument(
        "--primitives_out", 
        help="list of primitive names; Default: list_primitives.txt")
    parser.add_argument(
        "--max_depth", 
        help="max depth for the generated random tree; Default: 10", type=int)
    parser.add_argument(
        "--pop_size", 
        help="number of generated random trees; Default: 10", type=int)


    args = parser.parse_args()


    if not args.trees_out:
        trees_filename = "expressions.txt"
    else:
        trees_filename = args.trees_out

    if not args.primitives_out:
        primitives_filename = "list_primitives.txt"
    else:
        primitives_filename = args.primitives_out

    if not args.max_depth:
        max_depth = MAX_DEPTH
    else:
        max_depth = args.max_depth

    if not args.pop_size:
        pop_size = POP_SIZE
    else:
        pop_size = args.pop_size

        
    main(args.fit_in, trees_file=trees_filename,
         primitives_file=primitives_filename,
         popsize=pop_size, max_depth=max_depth)
