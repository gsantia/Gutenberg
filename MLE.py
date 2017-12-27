from __future__ import division
from collections import Counter, defaultdict
import math, re, random, sys, json
import numpy as np
from scipy.optimize import minimize

booknum = sys.argv[1]

def tokenize(book, space = False):
    """tokenize the book into distinct words"""
    book = re.sub("[ ]+", " ", book.decode('utf-8'))
    tokens = []
    for token in re.split("(["+chars+"0-9\'\-]+)", book):
        if re.search("(["+chars+"0-9]+)", token):
            for new_token in re.split("(^-*|-*$)", token):
                if new_token:
                    if new_token[0] == "-":
                        if space:
                            tokens.extend(new_token)
                    else:
                        tokens.append(new_token)
        else:
            if space:
                tokens.extend(token)
    return tokens

def model(ranks, n, t):
    """returns tuple of constant and list of (r+n)^t with r = 1, ..., N"""
    unnormed = (ranks + n)**t
    constant = 1 / (sum(unnormed))
    return unnormed, constant

def log_likelihood(x, M, fs, ranks):
    """returns log likelihood of the model defined by n, t"""
    n, t = x[0], x[1]
    unnormed, constant = model(ranks, n, t)

    log_L = M * np.log10(constant) + sum(fs * np.log10(unnormed))
    return -log_L

def mandelbrot_fit(path, space = False):

    book = ""
    M = 0   #number of words in the book

    with open(path, 'r') as file:
        word_counts = Counter()

        #read the text from the book
        for line in file:
            raw_words = tokenize(line, space = space)

            for word in raw_words:
                word_counts[word] += 1
                M += 1


    ranks = np.array(range(1, len(word_counts) + 1))
    words, fs  = zip(*word_counts.most_common())

    fs = np.array(fs)

    #now perform the MLE
    result = minimize(log_likelihood,  x0  = (2.7, -1), args = (M, fs, ranks), method='Nelder-Mead')
    unnormed, constant = model(ranks, result.x[0], result.x[1])

    return words, result, ranks, fs, unnormed, constant, M

def analysis(fs, M, constant, unnormed):
    """perform the calculations for cross_entropy, shannon, and KLD"""
    cross_entropy = -sum((fs / M) * np.log10(constant * unnormed))
    shannon = -sum((fs / M) * np.log10(fs / M))
    KLD = cross_entropy - shannon
    return  cross_entropy, shannon, KLD

def get_KLD(path, space, mandelbrot):
    """returns a tuple (words, fs, n, t, KLD)"""
    words, result, ranks, fs, f_hat, C, M = mandelbrot_fit(path, space)

    if mandelbrot:  #if we're looking at the mandelbrot model
        n, t = result.x
        unnormed, constant = model(ranks, n, t)
        cross_entropy, shannon, KLD = analysis(fs, M, constant, unnormed)

    else:   #the Simon model is quite different
        N = len(fs)
        t = (N / M) - 1
        n = 0

        for word in words:
            if re.search("[a-zA-Z0-9]", word):
                break
            n += 1
            ranks = np.array(range(1, N+1))

        #again calculate cross entropy, shannon, and KLD
        simon_factors = ((ranks + t) / N)**t
        simon_constant = 1 / sum(simon_factors)

        #interpreting one model from the perspective of the other
        n -= 1 + t

        cross_entropy, shannon, KLD = analysis(fs, M, simon_constant, simon_factors)

    return words, fs, n, t, KLD

################################################################################################################
# IMPLEMENTATION
################################################################################################################


if __name__ == "__main__":

    with open("chars.txt", "r") as f:
        chars = f.read().strip().decode("utf-8")
        chars = re.sub(" ", "", chars)

    #the path of the book is dependent on the CLI argument for book number
    path = r"/data/gutenbergAgain/books/ " + str(booknum) + ".txt"

    #store all the information we need in a dictionary
    book_data = {}

    words, fs, n1, t1, KLD1 = get_KLD(path, space = False, mandelbrot = True)

    #run the analysis again, but this time including "space" as a word
    words, fs, n2, t2, KLD2 = get_KLD(path, space = True, mandelbrot = True)

    #now we compare the previous two results to those from the Simon model, with space
    #t3 is the scaling exponent if from perfect Simon model -(1 - N/M) and or ([n+theta]/N)^theta
    words, fs, n3, t3, KLD3 = get_KLD(path, space = True, mandelbrot = False)

    #store the words and their counts in a single dictionary
    word_counts = defaultdict(list)
    for word, count in zip(words, fs):
        word_counts[count].append(word)

    #create the dict
    book_data = {
                    "word_counts": word_counts,
                    "Mandel": [n1, t1, KLD1],
                    "Mandel_space": [n2, t2, KLD2],
                    "Simon": [n3, t3, KLD3],
                }

    # print out the booknum, ns, ts, and KLDs
    with open("allBooks.tsv", "a") as f:
        n1, n2, n3, t1, t2, t3, KLD1, KLD2, KLD3 = map(str, [n1, n2, n3, t1, t2, t3, KLD1, KLD2, KLD3])
        tab_string1 = fake_booknum + '\t'+ n1 + '\t' + n2 + '\t' + n3 + '\t' + t1 + '\t' + t2
        tab_string2 = '\t' + t3 + '\t' + KLD1 + '\t' + KLD2 + '\t' + KLD3
        full_string = tab_string1 + tab_string2
        f.write(full_string)

    #now write out the book_data dictionary as a JSON file
    filename = str(booknum) + ".json"
    with open(filename, 'wb') as f:
        f.writelines(json.dumps(book_data, sort_keys = True, indent = 4) + '\n')







