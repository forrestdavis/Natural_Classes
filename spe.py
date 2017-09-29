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

#TODO SKIP OVER NON INVENTORY SOUNDS
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
            print "INVENTORY ERROR with ", sound
            continue
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
        if not notGenerated:
            generated.append(sound)

    return generated

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

    write_rules(phonemes, allophones, rules, uf)

    return 0

#TODO: How do we account for intervocalic? There must
#be some way of checking the environment of allophones
#so that you distinguish not just the difference between
#uf and allophone environments, but also the fact 
#that vowel to the left as a rule would overgenerate
#A -> B / C
def make_rules(feats, contexts, uf, allophones):

    rules = {}

    inv = generate_inventory(contexts, allophones) 

    feat_contexts = general_feat_contexts(feats, inv, contexts, allophones)
    sides = contrastive_side(feat_contexts, uf, allophones)
    if not sides:
        feat_contexts = specific_feat_contexts(feats, 
                inv, contexts, allophones)
        sides = contrastive_side(feat_contexts, uf, allophones)

    group = [uf] + allophones
    A = is_natural_class(feats, inv, [uf])
    print A
    for allophone in allophones:
        rule = [A]
        if allophone == uf:
            continue
        side = sides[allophone]
        if side == 'b':
            C = [feat_contexts[allophone]['l'], 
                    '__', feat_contexts[allophone]['r']]
        if side == 'r':
            C = ['__', feat_contexts[allophone]['r']]
        if side == 'l':
            C = [feat_contexts[allophone]['l'], '__']

        B = is_natural_class(feats, inv, [allophone])
        tmp = []
        for feat in B:
            #print feats[uf]
            if feat not in feats[uf]:
                tmp.append(feat)
        B = tmp
        rule.append(B)
        rule.append(C)
        rules[allophone] = rule

    return rules

def specific_feat_contexts(feats, inv, contexts, allophones):

    specific_feat_con = {}
    for sound in allophones:
        sound_l = contexts[sound]['l']
        sound_r = contexts[sound]['r']
        feat_l = is_natural_class(feats, inv, sound_l)
        feat_r = is_natural_class(feats, inv, sound_r)

        specific_feat_con[sound] = {}
        specific_feat_con[sound]['l'] = feat_l
        specific_feat_con[sound]['r'] = feat_r

    return specific_feat_con

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
            elif '-' == l:
                tmp = '!'
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
            return []

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
        inventory.append(allophone)
        for sound in contexts[allophone]['l']:
            if sound == '#' or sound == "-":
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


def write_rules(phonemes, allophones, rules, uf):

    print "Given the following group of sounds:", phonemes+allophones
    print "The following information was determined:\n"
    print "------------------------------------------"
    print "CONTRASTIVE: "
    if phonemes:
        print phonemes
    print "------------------------------------------"
    print "------------------------------------------"

    print "ALLOPHONES WITH RULES:"
    print '\t', uf, "AS UNDERLYING FORM"
    for allophone in allophones:
        if allophone == uf:
            continue
        print allophone+":"
        rule = rules[allophone]
        print rule[0], "---->", rule[1], "/", rule[2]
        print "------------------------------------------"


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

    return allophones, phonemes


if __name__ == "__main__":

    features = "features"
    inventory = "homework3_inv"
    words = "homework3_words"
    group = ['Ln', 'N']
    if len(sys.argv) == 2:
        words = "words"
        inventory = "chapter10_inv"
        group = ['r', 'R', 'r*r', ':R']

    generate_rules(features, inventory, words, group)

    #group = ['tS', 'b', 'v', 'f', 'd', 'm', 'z']
    group = ['N']
    print group, is_natural_class(features, inventory, group)

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
