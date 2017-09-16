
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

#TODO: This will take as input a collection of sounds and then 
#returns the list of distinctive features if true, else []
#TODO: FIX ERROR. NOT  PRODUCING MINIMUM SET OF FEATURES
def is_natural_class(features, inventory, group):
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

    produced = inv
    '''
    for i in range(distinct_feats):
        if 

    for d_feats in distinct_feats:
        generated = generate_sounds(feats, inv, [d_feats])
        print generated
    '''

    return 0

def generate_sounds(features, inventory, distinct_feats):

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

#TODO: This will take as input a sound inventory for a language
#returns the possible natural classes and their distinctive features
#as specified by the feature file
def generate_natural_class(feats, inventory):

    return 0

if __name__ == "__main__":

    features = "features.txt"
    inventory = "inventory.txt"
    #group = ['e', 'o', 'E', 'O']
    group = ['1', 'a']
    is_natural_class(features, inventory, group)

    distinct_feats = ['+Back', '-ATR']
    print generate_sounds(features, inventory, distinct_feats)
