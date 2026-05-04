# import required modules
from copy import deepcopy
from sys import exception
from tabnanny import check
import spacy
import textacy
nlp = spacy.load("en_core_web_sm")
import re
from nltk.tokenize import word_tokenize
import nltk

nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

positive_words = [
    # Verbs
    "loved", "enjoyed", "liked", "like", "adored", "relished", "cherished", 
    "appreciated", "treasured", "favored", "recommended", "celebrated","intoxicating",
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
    "atrocious", "abysmal", "lousy", "dismal","confusing"
]

def check_word(word, sentences, user_pref=None):
    # Initialize the dictionary if not provided to avoid mutable default arg bugs
    if user_pref is None:
        user_pref = {}
        
    # Finding sentence in word
    sentences = sentences.split(".")
    
    #Remove all special character's like Apostrophe's commas, etc...
    sentences = [
        re.sub(r'[^\w\s]', ' ', sentence.lower()).replace('\n', ' ') 
        for sentence in sentences
    ]

    word = word.lower()
    print("word", word)
    
    # 2. Find the matches
    # We only need to call .lower() once per check
    sentence_in = [
        sentence.lower() 
        for sentence in sentences
        if word in sentence.lower()
    ]
    print(sentence_in)
    
    if not sentence_in:
        return user_pref # Exit early if no matches found to prevent index errors
        
    sentence_list = sentence_in[0].split(" ")
    
    try:
        # if word has multiple characters
        if len(word.split(" ")) > 1:
            word_to_sent = (word.split(" "))
            if(sorted(word_to_sent) == sorted(list(set(word_to_sent) & set(sentence_list)))):
                fpnt = sentence_list.index(word_to_sent[-1])
                bpnt = sentence_list.index(word_to_sent[0])
                print("Pointers:",fpnt, bpnt)
        else:    
            fpnt = sentence_list.index(word)
            bpnt = sentence_list.index(word)
    except Exception as e:
        return user_pref
        
    sentence_in = " ".join(sentence_in)
    sentence_in = sentence_in.split(" ")
    
    # Find the closest positive or negative word from word
    for i in range(len(sentence_in)):
        
        print(sentence_in[fpnt], sentence_in[bpnt])
        if fpnt < len(sentence_in) - 1:
            fpnt += 1
        if bpnt > 0:
            bpnt -= 1
            
        if (sentence_in[fpnt] in positive_words or sentence_in[bpnt] in positive_words):
            if (sentence_in[fpnt] in ["liked", "like", "love", "loved"]) or (sentence_in[bpnt] in ["liked", "like", "love", "loved"]):
                print("Has LIKED or LOVED")
                flist = [w.replace('\n', '') for w in sentence_in[:fpnt]]
                blist = [w.replace('\n', '') for w in sentence_in[:bpnt]]
                print(flist[:2], blist[:2])
                if("didn" in flist[:2] or "didn" in blist[:2]):
                    user_pref[word] = -1
                    break
                else:                
                    user_pref[word] = 1
                    break
            user_pref[word] = 1
            break
            
        if (sentence_in[fpnt] in negative_words or sentence_in[bpnt] in negative_words):
            user_pref[word] = -1
            break            
        
    print("User Pref:", user_pref)
    return user_pref


def analyze_text(text, user_pref=None, country_Pref=None):
    # Initialize the dictionaries if not provided
    if user_pref is None:
        user_pref = {}
    if country_Pref is None:
        country_Pref = {}

    travelDoc = nlp(text)

    for ent in travelDoc.ents:
        print(ent.text, ent.label_)
        if(ent.label_ == 'LOC' or ent.label_ == "GPE"):
            # Pass user_pref into the check_word function
            check_word(ent.text, text, user_pref)
            
    country_Pref = deepcopy(user_pref)
    

    tagged_words = word_tokenize(text)
    tagged_words = nltk.pos_tag(tagged_words)
    for word, tag in tagged_words:
        if tag.startswith('NN'):
            check_word(word, text, user_pref)

    

        
    return deepcopy(user_pref), deepcopy(country_Pref)