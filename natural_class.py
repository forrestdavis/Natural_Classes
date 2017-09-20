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

#Function that takes as input a file of words
#and returns a dictionary key: value
#sound: [[to_left, to_right], [to_left, to_right]]
def generate_contexts(features, words_file):

    words = open(words_file, "r")

    contexts = {}
    for word in words:
        word.strip()
        if word:
            if word[0] == "#":
                continue
            word = word.split()
            for x in range(len(word)):
                context = []
                if x == 0:
                    context.append("#")
                if len(context) == 0:
                    context.append(word[x-1])
                if x == len(word) - 1:
                    context.append("#")
                else:
                    context.append(word[x+1])

                if word[x] not in contexts:
                    contexts[word[x]] = [context]
                else:
                    if context not in contexts[word[x]]:
                        contexts[word[x]].append(context)

    words.close()
    return contexts

#NOTE: For one sided context:
#
#Natural class of just context within the inventory yields
#the correct environment for the rule
#Further the intersection of the environment
#and the distinct features for environment+sound is the change
def generate_rules(features, inventory, word_file, group):
    
    contexts = generate_contexts(features, word_file)
    print contexts['Ln']
    print contexts['N']

    side = determine_env_dir(contexts, group)
    print side

    return 0

#Function that takes as input a set of contexts and a group
#of sounds you want to look at 
#Returns 'c' if contrastive sounds, 'b' if both left and right 
#are different for the sounds, 'l' if just left, 'r' if just right
#
#TODO: error with values return
def determine_env_dir(contexts, group):
    
    seen_pairs = []
    values = []
    for sound in group:
        #Create array of [[sounds to left], [sounds to right]]
        #populate with first element of context list
        l = contexts[sound][0][0]
        r = contexts[sound][0][1]
        l_r_context = [[l], [r]]
        #If more than one context continue population l_r_context
        if len(contexts[sound]) > 1:
            for y in range(1, len(contexts[sound])):
                l = contexts[sound][y][0]
                r = contexts[sound][y][1]
                #If sound not in current array add
                if l not in l_r_context[0]:
                    l_r_context[0].append(l)
                if r not in l_r_context[1]:
                    l_r_context[1].append(r)

        #Now compare to rest of sounds skipping over the sound 
        #already seen
        for sound2 in group:
            #Skip over x x pairs
            if sound2 == sound:
                continue
            #This allows us to see a pair of sounds only once instead
            #of once for x y and another for y x
            seen_pair = [sound, sound2]
            seen2_pair = [sound2, sound]
            if seen_pair in seen_pairs:
                continue
            if seen2_pair in seen_pairs:
                continue
            else:
                #Else add pair to seen
                seen_pairs.append(seen_pair)
                not_l = 0
                not_r = 0
                #if any environment then cant be left
                if '-' in l_r_context[0]:
                    not_l = 1

                #look at contexts for 2nd sound
                for context in contexts[sound2]:
                    l = context[0]
                    r = context[1]
                    #If left context in first sound env, can't be left
                    if l in l_r_context[0]:
                        not_l = 1
                    #If right context in first sound env, can't be right
                    if r in l_r_context[1]:
                        not_r = 1
                    #If any environment then cant be right
                    if r == '-':
                        not_r = 1

                #If neither l nor r is contrastive, then must be 
                #seperate phonemes
                if not_l and not_r:
                    seen_pair.append('c')
                #If both work then need to handle this seperately
                if not not_l and not not_r:
                    seen_pair.append('b')
                #If just right then must be r
                if not not_r:
                    seen_pair.append('r')
                #If just left then must be l
                else:
                    seen_pair.append('l')
                values.append(seen_pair)
    return values

if __name__ == "__main__":

    features = "features.txt"
    #inventory = "inventory.txt"
    inventory = "homework3_inv.txt"
    output = "h3"
    words = "words.txt"

    group = ['e', 'i', 'j', 'Ln']

    print group, is_natural_class(features, inventory, group)

    group = ['Ln', 'N', 'n']
    generate_rules(features, inventory, words, group)

    '''
    group = ['p', 'pH']
    print group, is_natural_class(features, inventory, group)

    distinct_feats = is_natural_class(features, inventory, group)

    print generate_sounds(features, inventory, distinct_feats)
    distinct_feats.append('?SG')
    print generate_sounds(features, inventory, distinct_feats)


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
    '''
