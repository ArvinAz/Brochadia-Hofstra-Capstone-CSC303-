# import required modules
from copy import deepcopy
from tabnanny import check
import spacy
import textacy
nlp = spacy.load("en_core_web_sm")

positive_words = [
    # Verbs
    "loved", "enjoyed", "liked", "like", "adored", "relished", "cherished", 
    "appreciated", "treasured", "favored", "recommended", "celebrated",
    # Adjectives
    "amazing", "fantastic", "wonderful", "great", "excellent", 
    "fun", "perfect", "awesome", "incredible", "delightful", 
    "thrilling", "captivating", "fascinating", "beautiful", "superb",
    "breathtaking", "unforgettable", "stellar", "brilliant"
]

travel_companions = [
    "girlfriend", 
    "boyfriend", 
    "spouse", 
    "partner", 
    "fiancé", 
    "fiancée", 
    "new date",
    "parents", 
    "siblings", 
    "children", 
    "grandparents", 
    "cousins", 
    "aunts", 
    "uncles", 
    "in-laws",
    "best friends", 
    "casual friends", 
    "acquaintances", 
    "childhood friends", 
    "roommates", 
    "mutual friends",
    "classmates", 
    "study group members", 
    "co-workers", 
    "colleagues", 
    "business partners", 
    "mentors", 
    "mentees",
    "club members", 
    "hobby group members", 
    "online friends", 
    "volunteer group members", 
    "organized tour group members",
    "pet", 
    "yourself"
]

negative_words = [
    # Verbs
    "hated", "disliked", "dislike","despised", "loathed", "detested", 
    "dreaded", "regretted", "avoided", "endured", "suffered", "resented",
    # Adjectives
    "awful", "terrible", "horrible", "boring", "miserable", 
    "bad", "disappointing", "exhausting", "unpleasant", "worst", 
    "dull", "underwhelming", "overrated", "frustrating", "mediocre",
    "atrocious", "abysmal", "lousy", "dismal"
]

user_pref =  {}
country_Pref = {}

def remove_special_characters(sentence):
    
    return sentence.replace(",", " ").replace("\n", " ").replace("'", " ").replace("\"", " ").replace(".", " ").replace("!", " ").replace("?", " ").replace(":", " ").replace(";", " ").replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ").replace("{", " ").replace("}", " ").replace("`", " ").replace("~", " ").replace("^", " ").replace("*", " ").replace("+", " ").replace("-", " ").replace("_", " ").replace("=", " ").replace("|", " ").replace("\\", " ").replace("/", " ").replace("<", " ").replace(">", " ").replace(" ", " ")

def check_word(word, sentences):
    # Finding sentence in word
    
    sentences = sentences.split(".")
    
    #Remove all special character's like Apostrophe's commas, etc...
    sentences = [sentence.replace(",", " ").replace("'", " ").replace("\"", " ").replace(".", " ").replace("!", " ").replace("?", " ").replace(":", " ").replace(";", " ").replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ").replace("{", " ").replace("}", " ").replace("`", " ").replace("~", " ").replace("^", " ").replace("*", " ").replace("+", " ").replace("-", " ").replace("_", " ").replace("=", " ").replace("|", " ").replace("\\", " ").replace("/", " ").replace("<", " ").replace(">", " ").replace(" ", " ") for sentence in sentences]
    #print(sentences)
    
    word = word.lower()
    sentence_in = [sentence.lower() for sentence in sentences if word in sentence.lower()]
    print(sentence_in, sentences)
    #print(sentence_in)
    sentence_list = sentence_in[0].split(" ")
    
    

    
    try:
        # if word has multiple characters
        if len(word.split(" ")) > 1:
            word_to_sent = (word.split(" "))
            #print("Multiple characters")
            #print(sorted(word_to_sent) == sorted(list(set(word_to_sent) & set(sentence_list))))
            if(sorted(word_to_sent) == sorted(list(set(word_to_sent) & set(sentence_list)))):
                fpnt = sentence_list.index(word_to_sent[-1])
                bpnt = sentence_list.index(word_to_sent[0])
                #print("Pointers:",fpnt, bpnt)
        else:    
            #print("Single character")
            fpnt = sentence_list.index(word)
            bpnt = sentence_list.index(word)
            #print("Word: ", word, "FPNT: ", fpnt, "BPNT: ", bpnt)
    except ValueError:
        print("Value Error")
        return
    #print(fpnt, bpnt)
    #sentence_in = sentence_in[0].split(word)
    #print("Sentence in: ", sentence_in, "FPNT: ", fpnt, "BPNT: ", bpnt)
    sentence_in = " ".join(sentence_in)
    sentence_in = sentence_in.split(" ")
    # Find the closest positive or negative word from word
    #print(sentence_in)
    for i in range(len(sentence_in)):
        print(fpnt, bpnt)
        print(sentence_in[fpnt], sentence_in[bpnt])
        if fpnt < len(sentence_in) - 1:
            fpnt += 1
        if bpnt > 0:
            bpnt -= 1
        #print(sentence_in[bpnt], sentence_in[fpnt])
        if (sentence_in[fpnt] in positive_words or sentence_in[bpnt] in positive_words):
            # Make the word have negative score if didnt appears behind either the fpnt or bpnt
            #print("Positive word: ", "".join([sentence_in[fpnt - 1], sentence_in[fpnt - 2]]), sentence_in[fpnt], "".join([sentence_in[bpnt - 1], sentence_in[bpnt - 2]]), sentence_in[bpnt])
            
            if (sentence_in[fpnt] in ["liked", "like", "love", "loved"]) or (sentence_in[bpnt] in ["liked", "like", "love", "loved"]):

                print("Has LIKED or LOVED")
                flist = [word.replace('\n', '') for word in sentence_in[:fpnt]]
                blist = [word.replace('\n', '') for word in sentence_in[:bpnt]]
                print(flist[:2], blist[:2])
                if("didn" in flist[:2] or "didn" in blist[:2]):
                    user_pref[word] = -1
                    break;
                else:                
                    user_pref[word] = 1
                    break;
            user_pref[word] = 1
            break;
            
        if (sentence_in[fpnt] in negative_words or sentence_in[bpnt] in negative_words):
            #print("Negative word: ", sentence_in[fpnt], sentence_in[bpnt])
            user_pref[word] = -1
            break            
        
    print("User Pref:", user_pref)

    






text = ("I Loved riding and swim around the beautiful Lake Burley Griffin and exploring the grand Parliament House. "
"I Didn't Like The freezing wind on Mount Ainslie and how early the city shuts down at night!")
print()
#print(check_word("cycling", text ))
#print(user_pref)

def analyze_text(text):
    global user_pref, country_Pref

    user_pref = {}
    country_Pref = {}

    travelDoc = nlp(text)

    for ent in travelDoc.ents:
        print(ent.text, ent.label_)
        if(ent.label_ == 'LOC' or ent.label_ == "GPE"):
            check_word(ent.text , text)
    country_Pref = deepcopy(user_pref)
    print("Country Pref:", country_Pref)
    # returns a document of object


    for chunk in travelDoc.noun_chunks:
        print("Noun Chunk: ", remove_special_characters(str(chunk)))
        if chunk in travel_companions:
            continue
        check_word(remove_special_characters(str(chunk)), text)


    # Searching Verbs
    patterns = [{"POS": "VERB"}]

    about_talk_doc = textacy.make_spacy_doc(
            text, lang="en_core_web_sm"
    )
    verb_phrases = textacy.extract.token_matches(
            about_talk_doc, patterns=patterns
    )

    for chunk in verb_phrases:
        if chunk.text.lower() in positive_words or chunk.text.lower() in negative_words:
            continue

        check_word(chunk.text, text)
    return deepcopy(user_pref), deepcopy(country_Pref)

'''
print(analyze_text("My trip down to the Sunshine State was a wild mix of beautiful coastlines and absolute chaos."
"Loved: Exploring the vibrant nightlife and incredible Cuban food in Miami's Little Havana, plus the thrill of seeing alligators on an airboat tour through the Everglades."
"Didn't Like: The suffocating afternoon humidity, the terrifyingly massive mosquitoes, and the endless, exhausting lines at the Orlando theme parks!"))
'''
