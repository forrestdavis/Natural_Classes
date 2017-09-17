from itertools import combinations

#Creates a dictionary of key: value, sound: features
#from a feature file
def load_features(filename):
    data = open(filename, "r")

    feats = {}
    for line in data:
        line = line.strip()
        if line:
            if line[0] != "#":
                line = line.split()
                feats[line[0]] = line[1:]

    data.close()
    return feats

#Loads inventory from a file containing all the sounds
#returns a list
def load_inventory(filename):
    data = open(filename, "r")

    inv = []
    for line in data:
        line = line.strip()
        if line:
            if line[0] != "#":
                line = line.split()
                inv.append(line[0])

    data.close()
    return inv

#This will take as input a collection of sounds and then 
#returns the list of distinctive features if true, else []
#If verbose is True, then will return unmaximized distinct
#features and maximized
def is_natural_class(features, inventory, group, verbose=False):
    inv = load_inventory(inventory)
    feats = load_features(features)

    distinct_feats = []
    for x in range(len(group)):
        sound = group[x]
        if sound not in inv:
            print "ERROR with ", sound
            break
        if x == 0:
            distinct_feats = feats[sound]

        else:
            tmp = []
            for y in range(len(distinct_feats)):
                if distinct_feats[y] in feats[sound]:
                    tmp.append(distinct_feats[y])
            distinct_feats = tmp

    #Checks to see that the set of shared features only generates
    #the group
    generated = generate_sounds(feats, inv, distinct_feats) 
    notSet = 0
    for s in generated:
        if s not in group:
            notSet = 1
    if notSet:
        distinct_feats = []

    #If verbose return the full set and minimum set
    if verbose:
        return distinct_feats, check_minumum(feats, inv, group, distinct_feats)

    #If valid set, then minimize feature space
    if distinct_feats:
        distinct_feats = check_minumum(feats, inv, group, distinct_feats)

    return distinct_feats

#Function that takes a set of a group of sounds and their distinct
#features and produces all combinations of the sounds to return the 
#minimum set of features to produce only those sounds.
def check_minumum(feats, inv, group, distinct_feats):

    #Generates all combinations of features (2^N)
    possible_feats = (sum([map(list, combinations(distinct_feats, i)) 
        for i in range(len(distinct_feats)+1)], []))

    minimum_set = distinct_feats
    for possible in possible_feats:
        sounds = generate_sounds(feats, inv, possible)
        correctSet = 1
        for sound in sounds:
            if sound not in group:
                correctSet = 0
        if correctSet:
            if len(possible) < len(minimum_set):
                minimum_set = possible

    return minimum_set

#Function that generates sounds from a set  of features and
#a langauage inventory
def generate_sounds(features, inventory, distinct_feats):

    #This is to allow both the passing of a feature/inventory
    #file or an already created feats/inv set
    if type(features) == str:
        feats = load_features(features)
    if type(inventory) == str:
        inv = load_inventory(inventory)
    if type(features) == dict:
        feats = features
    if type(inventory) == list:
        inv = inventory 

    generated = []
    for sound in inv:
        notGenerated = 0
        for d_feats in distinct_feats:
            if d_feats not in feats[sound]:
                notGenerated = 1
        '''
        for feat in feats[sound]:
            if feat not in distinct_feats:
                notGenerated = 1
        '''
        if not notGenerated:
            generated.append(sound)

    return generated

#TODO: This will take as input a sound inventory for a language
#returns the possible natural classes and their distinctive features
#as specified by the feature file
def generate_natural_class(feats, inventory):

    return 0

#Function that returns information about the minimizations
#of distinct feature sets from a list of groups of sounds
def diagnostics(features, inventory, groups, output_file):
    
    output = open(output_file, 'w')
    counts = {}
    combinations = []
    for group in groups:
        p_feats, min_feats = is_natural_class(features, 
                inventory, group, True)
        output.write("Group: "+'['+",".join(group) +']')
        output.write("\n\tBefore Minimization: "+'['+",".join(p_feats) +']')

        for feat in p_feats:
            if feat not in min_feats:
                if feat not in counts:
                    counts[feat] = 1
                else:
                    counts[feat] += 1
                output.write("\n\tRemoved Feature: "+feat)
        output.write("\n\tAfter Minimization: "+'['+','.join(min_feats)+']')

        output.write("\n\tNumber of combinations "+str(2**len(p_feats)))

        output.write("\n---------------------------------\n")

        combinations.append(2**len(p_feats))

    output.write("Counts for each removed feature:\n")
    for f in counts:
        output.write(f+": "+str(counts[f])+'\n')

    output.write("\n---------------------------------\n")

    output.write("Average number of considered combinations: "+ 
            str(sum(combinations)/len(combinations)))

    output.close()

if __name__ == "__main__":

    features = "features.txt"
    inventory = "inventory.txt"
    output = "output"

    group = ['p']
    print group, is_natural_class(features, inventory, group)


    groups = [['p', 'pH', 'b', 'f', 'v', 'm'],
            ['pH', 'tH', 'tSH', 'kH', 'qH'],
            ['k', 'q', 'kH', 'qH'],
            ['b', 'd', 'dZ', 'g'],
            ['s', 'z', 'S', 'Z'],
            ['m', 'n', 'Ln', ':N', 'N', 'w', 'l', ':R', 'j'], 
            ['Ln', ':R'], 
            ['1', 'a'],
            ['e', 'o', 'E', 'O'],
            ['tH', 'd']]
    diagnostics(features, inventory, groups, output)
