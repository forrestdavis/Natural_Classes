from itertools import combinations
from sets import Set
import sys

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

    feats = features
    inv = inventory
    if type(features) == str:
        feats = load_features(features)
    if type(inv) == str:
        inv = load_inventory(inventory)

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
#sound: ['l': [s1 ...] 'r' [s2 ...]]
def generate_contexts(words_file):

    words = open(words_file, "r")

    contexts = {}
    for word in words:
        word.strip()
        if word:
            #ignore comments
            if word[0] == "#":
                continue
            word = word.split()
            for x in range(len(word)):
                l = ''
                r = '' 
                if x == 0:
                    l = '#'
                else:
                    l = word[x-1]

                if x == len(word)-1:
                    r = '#'
                else:
                    r = word[x+1]

                if word[x] not in contexts:
                    contexts[word[x]] = {}
                    contexts[word[x]]['l'] = [l]
                    contexts[word[x]]['r'] = [r]
                else:
                    if l not in contexts[word[x]]['l']:
                        contexts[word[x]]['l'].append(l)
                    if r not in contexts[word[x]]['r']:
                        contexts[word[x]]['r'].append(r)


    words.close()
    return contexts

#NOTE: For one sided context:
#
#Natural class of just context within the inventory yields
#the correct environment for the rule
#Further the intersection of the environment
#and the distinct features for environment+sound is the change
def generate_rules(features, inventory, word_file, group):
    
    contexts = generate_contexts(word_file)
    feats = load_features(features)
    
    allophones, phonemes = prune_phonemes(group, contexts)
    
    #Terminate if there are no allophones
    if not allophones:
        print phonemes
        return 1

    uf = posit_underlying_form(feats, allophones)
    rules = make_rules(feats, contexts, uf, allophones)

    '''
    write_rules(phonemes, allophones, rules, group, UF)
    '''

    return 0

#TODO: How do we account for intervocalic? There must
#be some way of checking the environment of allophones
#so that you distinguish not just the difference between
#uf and allophone environments, but also the fact 
#that vowel to the left as a rule would overgenerate
def make_rules(feats, contexts, uf, allophones):

    inv = generate_inventory(contexts, allophones) 

    feat_contexts = general_feat_contexts(feats, inv, contexts, allophones)
    sides = contrastive_side(feat_contexts, uf, allophones)
    print sides

    return 0

#Function that returns the contexts of the allophones, but rather
#than a group of sounds, returns the general feature type.
#The possible general feature types are V, C, #, MISMATCH
#The return value is {allophone: {'l': FEAT, 'r': FEAT}}
def general_feat_contexts(feats, inv, contexts, allophones):

    general_feat_con = {} 
    for sound in allophones:
        sound_l = contexts[sound]['l']
        sound_r = contexts[sound]['r']

        general_l = []
        general_r = []

        for l in sound_l:
            tmp = '' 
            if '#' == l:
                tmp = '#'
            else:
                f = feats[l]
                if "+Syllabic" in f:
                    tmp = 'V'
                else:
                    tmp = 'C'
            if not general_l:
                general_l.append(tmp)
            else:
                if tmp not in general_l:
                    general_l = ["MISMATCH"]
                    break

        for r in sound_r:
            tmp = '' 
            if '#' == r:
                tmp = '#'
            else:
                f = feats[r]
                if "+Syllabic" in f:
                    tmp = 'V'
                else:
                    tmp = 'C'
            if not general_r:
                general_r.append(tmp)
            else:
                if tmp not in general_r:
                    general_r = ["MISMATCH"]
                    break


        general_feat_con[sound] = {}
        general_feat_con[sound]['l'] = general_l
        general_feat_con[sound]['r'] = general_r

    return general_feat_con



#Function that calculates which side of allophone is
#contrastive. Returns {allophone: b/r/l}
def contrastive_side(feat_contexts, uf, allophones):

    sides = {}
    uf_l = feat_contexts[uf]['l']
    uf_r = feat_contexts[uf]['r']
    for allophone in allophones:
        if allophone == uf:
            continue
        allophone_l = feat_contexts[allophone]['l']
        allophone_r = feat_contexts[allophone]['r']

        side = ''
        is_l = 0
        is_r = 0
        if allophone_l != uf_l:
            is_l = 1
        if allophone_r != uf_r:
            is_r = 1

        for sound in allophones:
            if(sound == allophone or
                    sound == uf):
                continue
            if is_l and not is_r:
                #If left context is same as left context of other
                #allophone then it must be both right and left
                if allophone_l == feat_contexts[sound]['l']:
                    is_r = 1
                    break

            elif is_r and not is_l:
                #If right context is the same as right context
                #of other allophones then it must be both left
                #and right
                if allophone_r == feat_contexts[sound]['r']:
                    is_l = 1
                    break

            #If both sides are contrastive, then pick one
            #that is different than other allophones
            else:
                if allophone_l == feat_contexts[sound]['l']:
                    is_l = 0
                    break
                if allophone_r == feat_contexts[sound]['r']:
                    is_r = 0
                    break

        if is_l and is_r:
            side = 'b'
        elif is_l:
            side = 'l'
        elif is_r:
            side = 'r'
        else:
            print "ERROR"

        sides[allophone] = side

    return sides

#Inventory for rule generation is not all possible sounds
#in the language but rather the sounds in the context
#of a set of possible allophones. This function
#returns such an inventory given the set of allophones
#and the contexts
def generate_inventory(contexts, allophones):

    inventory = []
    for allophone in allophones:
        for sound in contexts[allophone]['l']:
            if sound == '#':
                continue
            if sound not in inventory:
                inventory.append(sound)
        for sound in contexts[allophone]['r']:
            if sound == '#':
                continue
            if sound not in inventory:
                inventory.append(sound)
    return inventory 

#Function that posits an UF given a set of allophones and 
#their features. It does this by picking the allophone
#that would require the least amount of feature changes
#to generate the rest of the allophones.  
def posit_underlying_form(feats, allophones):

    min_feat_diff = 1000000
    possible_uf = '' 
    for allophone in allophones:
        total_feat_diff = 0
        for sound in allophones:
            if sound == allophone:
                continue
            f1 = Set(feats[allophone])
            f2 = Set(feats[sound])
            total_feat_diff += len(f1-f2)
        if total_feat_diff < min_feat_diff:
            min_feat_diff = total_feat_diff
            possible_uf = allophone

    return possible_uf


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
'''    
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
'''    

#Function that seperates phonemes from allophones
#Returns two lists, allophones and phonemes
#Makes an basic decision that if you have
#two things that are seperate phonemes and 
#this environment has an allophone, then only
#one can be in this allophonic relationship.
#Picks first element of phonemes to fulfill this
#role. 
def prune_phonemes(group, contexts):

    allophones = []
    phonemes = []
    for sound in group:
        sound_l = contexts[sound]['l']
        sound_r = contexts[sound]['r']
        for s in group:
            if s == sound:
                continue
            s_l = contexts[s]['l']
            s_r = contexts[s]['r']
            same_l = 1
            same_r = 1
            for x in sound_l:
                if x not in s_l:
                    same_l = 0
            for x in sound_r:
                if x not in s_r:
                    same_r = 0
            if same_l and same_r:
                if sound not in phonemes:
                    phonemes.append(sound)
                if s not in phonemes:
                    phonemes.append(s)
            else:
                #Only add allophone if two environment has a 
                #phoneme
                if(sound not in allophones
                        and sound not in phonemes):
                    allophones.append(sound)
                if(s not in allophones and
                        s not in phonemes):
                    allophones.append(s)
    #Add first element of phonemes to allophones if it is
    #in an allophonic relationship
    if allophones and phonemes:
        allophones.append(phonemes[0])

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

'''

if __name__ == "__main__":

    features = "features"
    words = "words"
    inventory = "chapter10_inv"
    group = ['r', 'R', 'r*r', ':R']
    if len(sys.argv) == 2:
        inventory = "homework3_inv"
        words = "homework3_words"
        group = ['Ln', 'N']

    generate_rules(features, inventory, words, group)

    #group = ['tS', 'b', 'v', 'f', 'd', 'm', 'z']
    #print group, is_natural_class(features, inventory, group)

    '''

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
