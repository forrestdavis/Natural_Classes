from itertools import combinations
from sets import Set

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

    side = determine_env_dir(contexts, group)
    
    allophones, phonemes = prune_phonemes(side)

    if allophones:
        UF = posit_underlying_form(features, contexts, allophones)
        print UF
        rules = []
        for pair in allophones:
            if UF in pair:
                rule = make_rule(features, inventory, contexts, pair, UF)
                if rule == 0:
                    print "FATAL ERROR GENERATING RULE FOR ALLOPHONES", pair
                    return 0
                rules.append(rule)

    write_rules(phonemes, allophones, rules, group, UF)

    return 1


def write_rules(phonemes, allophones, rules, group, UF):

    print "Given the following group of sounds:", group
    print "The following information was determined:\n"
    print "------------------------------------------"
    print "CONTRASTIVE: "
    for pair in phonemes:
        print pair[0], pair[1]
    print "------------------------------------------"

    print "ALLOPHONES WITH RULES GIVEN", UF, "AS UNDERLYING FORM"
    x = 0
    for pair in allophones:
        if x == len(rules):
            break
        if pair[0] != UF:
            print pair[0], "becomes", UF
        else:
            print pair[1], "becomes", UF
        print "\t Rule: "
        rule = rules[x]
        if pair[2] == "r":
            print rule[0], "--->", rule[1], "/", " __", rule[2]
        if pair[2] == "l":
            print rule[0], "--->", rule[1], "/", rule[2], "__"
        x += 1


#Function that takes feature file, inventory file, contexts, 
#allophone triplet as seen from prune_phonemes and the UF
#and returns a rule for generating the SF from UF.
#Return value is list [A, B, C] which is reduction of 
#A --> B / C
def make_rule(features, inventory, contexts, pair, UF):
    
    rule = []
    sound = pair[1]
    if pair[1] == UF:
        sound = pair[0]

    A = is_natural_class(features, inventory, UF)
    if not A:
        print "ERROR WITH GETTING DISTINCT FEATURES OF", UF
        return 0
    else:
        rule.append(A)

    group = []
    env = 0
    if pair[2] == "r":
        env = 1
    for context in contexts[sound]:
        group.append(context[env])
    C = is_natural_class(features, inventory, group)
    if not C:
        print "ERROR WITH GETTING DISTINCT FEATURES OF", group
        return 0

    group.append(sound)
    B = is_natural_class(features, inventory, group)

    tmp = []
    for element in B:
        if element in C:
            tmp.append(element)

    B = tmp
    if not B:
        print "ERROR WITH GETTING CHANGED FEATURE OF", UF, "TO", sound
        return 0

    rule.append(B)
    rule.append(C)

    return rule
    

#Function that seperates phonemes from allophones
#Returns two lists, allophones and phonemes
#of the form [sound1, sound2, type]
def prune_phonemes(side):

    allophones = []
    phonemes = []
    for pair in side:
        if pair[2] != 'c':
            allophones.append(pair)
        else:
            phonemes.append(pair)

    return allophones, phonemes

#Function that takes a file for features, a dictionary of contexts
#and the set of allophone pairs, and returns the underlying form
#
###
'''
The underlying form is the sound with the largest variety of features in 
its complementary distribution set. This is determined by taking each pair
of allophones, and the direction of its environment contrast. For each
allophone in the pair, we step through the contexts determined by the 
environment and use set union to determine the set of all features
associated with the sound in this context. These sets are compared, 
with the largest being compared to the global max set size. The sound
with the largest set of unioned features is the underlying form. This
is more easily seen with an example:

    Given the set of allophones: [[p, pH, r]]
    
    we grab each such triplet of information (in this case just the one)
    [p, pH, r]

    we start with the empty set feat1.
    we look at all the sounds occuring to the right of p (from the r flag)
    From this we pick out the set of each sound's features and union
    them together with feat1, to generate a set of all features associated
    with the right context of p

    we do the same thing for pH.

    if the set of feature contexts of p is larger than pH, then we posit
    that it is a possible underlying form. If we have seen no set
    larger than the set for p, then p is the assumed underlying form.
    A similar process occurs if pH is larger than p.

    At the end of looking at all allophone pairs, we should return the 
    phoneme that has the most diverse features in its context.
'''
####
def posit_underlying_form(features, contexts, allophones):

    feats = load_features(features)
    uf = ''
    largest_set = 0
    for pair in allophones:
        allo1 = pair[0]
        allo2 = pair[1]
        env = 0
        if pair[2] == "r":
            env = 1
        feat1 = Set([])
        for context in contexts[allo1]:
            sound = context[env]
            #Adding word boundary as a feature
            if sound == "#":
                tmp = Set(["+WB"])
            else:
                tmp = Set(feats[sound])
            feat1 = feat1 | tmp

        feat2 = Set([])
        for context in contexts[allo2]:
            sound = context[env]
            #Adding word boundary as a feature
            if sound == "#":
                tmp = Set(["+WB"])
            else:
                tmp = Set(feats[sound])
            feat2 = feat2 | tmp

        if len(feat1) > len(feat2):
            if len(feat1) > largest_set:
                largest_set = len(feat1)
                uf = allo1
        else:
            if len(feat2) > largest_set:
                largest_set = len(feat2)
                uf = allo2

    return uf


#Function that takes as input a set of contexts and a group
#of sounds you want to look at 
#Returns a list of [[sound1, sound2, env], ...], where env
#is one of four values: 'c' if contrastive sounds (seperate phonemes)
#'b' if both left and right environments are different, 'l' if
#just the the left enivronment is different, and 'r' if just
#the right is different
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
            elif seen2_pair in seen_pairs:
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
                value = [sound, sound2]
                if not_l and not_r:
                    value.append('c')
                #If both work then need to handle this seperately
                elif not not_l and not not_r:
                    value.append('b')
                #If just right then must be r
                elif not not_r:
                    value.append('r')
                #If just left then must be l
                else:
                    value.append('l')
                values.append(value)
    return values

if __name__ == "__main__":

    features = "features"
    #inventory = "inventory"
    inventory = "chapter10_inv"
    output = "h3"
    words = "words"

    group = ['r', 'R', 'r*r', ':R']
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
