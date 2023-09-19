import os
import csv
import re
import nltk
import enchant
import pandas as pd
import time

BASE = "Base"
NORMALIZATION_AND_TOKENIZATION = "NT"
REMOVE_STOP_WORDS = "R"
PORTER_STEMMER = "SP"
SNOWBALL_STEMMER = "SS"
LANCASTER_STEMMER = "SL"
LEMMATIZER = "L"
LEMMATIZER_AND_POS = "LT"


def find_uri(ontology):
    for ns_prefix, namespace in ontology.namespaces():
        if not ns_prefix:
            return namespace
    return ""


def create_folder(path):
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        return True
    else:
        return False


def create_document(document_path, header):
    if os.path.exists(document_path) and os.path.isfile(document_path):
        os.remove(document_path)
        # print("replace, file deleted")
    # else:
    # print("create, file not found")
    # create a new file
    with open(document_path, "w+", newline='') as f1:
        writer = csv.writer(f1)
        header = header
        writer.writerow(header)


# change to camel case to snake case
def change_to_snake_case(name):
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    name = pattern.sub(' ', name)
    name = repair_acronyms(name)
    return name


# example siteURL
def repair_acronyms(name):
    words = name.split(' ')
    result = []
    temp = ''
    # create a temp to store the word
    for word in words:
        if len(word) == 1:
            temp += word
        else:
            if temp:
                result.append(temp)
                temp = ''
            result.append(word)
    # add any remaining single-character words
    if temp:
        result.append(temp)
    return ' '.join(result)


# change British spelling to American spelling
def change_british_to_american(word):
    uk_dict = enchant.Dict("en_GB")
    us_dict = enchant.Dict("en_US")
    # check whether the word is british spelling
    suggestions = None
    if uk_dict.check(word) and not us_dict.check(word):
        suggestions = us_dict.suggest(word)
    # return american spelling
    return suggestions[0] if suggestions else word


# https://stackoverflow.com/questions/5843518/remove-all-special-characters-punctuation-and-spaces-from-string
def cleaning(name):
    # if symbols, change them to ' '
    name = re.sub(r'[^A-Za-z0-9]+', ' ', str(name))
    # if no symbols, it is a camel case and change it to snake case
    if " " not in name:
        name = change_to_snake_case(name)
    name = name.lower()
    name = change_british_to_american(name)
    # name = name.replace(" ", " and ")
    return name


def removing_stop_words(name):
    # converts the words in word_tokens to lower case and then checks whether they are present in stop words or not
    word_tokens = nltk.tokenize.word_tokenize(name)
    # print(word_tokens)
    stop_words = set(nltk.corpus.stopwords.words('english'))
    keywords = [w for w in word_tokens if not w in stop_words]
    name = ' '.join(keywords)
    return name


def removing_stop_words_reserve(name):
    r_reserved_words = reserved_words_dict[REMOVE_STOP_WORDS]
    # converts the words in word_tokens to lower case and then checks whether they are present in stop words or not
    word_tokens = nltk.tokenize.word_tokenize(name)
    # print(word_tokens)
    stop_words = nltk.corpus.stopwords.words('english')
    for i in r_reserved_words:
        if i in stop_words:
            stop_words.remove(i)
    keywords = [w for w in word_tokens if not w in stop_words]
    name = ' '.join(keywords)
    return name


def get_stemming(name, method):
    keywords = name.split()
    tag = nltk.pos_tag(keywords)
    strs = list()
    for name in keywords:
        if method == PORTER_STEMMER:
            stemmer = nltk.stem.PorterStemmer()
            name = stemmer.stem(name)
        if method == SNOWBALL_STEMMER:
            stemmer = nltk.stem.SnowballStemmer("english")
            name = stemmer.stem(name)
        if method == LANCASTER_STEMMER:
            stemmer = nltk.stem.LancasterStemmer()
            name = stemmer.stem(name)
        if method == LEMMATIZER:
            lmtzr = nltk.stem.wordnet.WordNetLemmatizer()
            name = lmtzr.lemmatize(name)
        if method == LEMMATIZER_AND_POS:
            lmtzr = nltk.stem.wordnet.WordNetLemmatizer()
            name = lmtzr.lemmatize(name, pos=penn2morphy(tag))
        strs.append(name)
    # return strs
    return ' '.join(strs)


def get_stemming_reserve(name, method):
    sp_reserved_words = reserved_words_dict[PORTER_STEMMER]
    ss_reserved_words = reserved_words_dict[SNOWBALL_STEMMER]
    sl_reserved_words = reserved_words_dict[LANCASTER_STEMMER]
    l_reserved_words = reserved_words_dict[LEMMATIZER]
    lt_reserved_words = reserved_words_dict[LEMMATIZER_AND_POS]
    keywords = name.split()
    tag = nltk.pos_tag(keywords)
    strs = list()
    for name in keywords:
        if method == PORTER_STEMMER:
            if name not in sp_reserved_words:
                stemmer = nltk.stem.PorterStemmer()
                name = stemmer.stem(name)
        if method == SNOWBALL_STEMMER:
            if name not in ss_reserved_words:
                stemmer = nltk.stem.SnowballStemmer("english")
                name = stemmer.stem(name)
        if method == LANCASTER_STEMMER:
            if name not in sl_reserved_words:
                stemmer = nltk.stem.LancasterStemmer()
                name = stemmer.stem(name)
        if method == LEMMATIZER:
            if name not in l_reserved_words:
                lmtzr = nltk.stem.wordnet.WordNetLemmatizer()
                name = lmtzr.lemmatize(name)
        if method == LEMMATIZER_AND_POS:
            if name not in lt_reserved_words:
                lmtzr = nltk.stem.wordnet.WordNetLemmatizer()
                name = lmtzr.lemmatize(name, pos=penn2morphy(tag))
        strs.append(name)
    # return strs
    return ' '.join(strs)


# converts Penn Treebank tags to WordNet
def penn2morphy(penntag):
    morphy_tag = {'NN': 'n', 'JJ': 'a',
                  'VB': 'v', 'RB': 'r'}
    try:
        return morphy_tag[penntag[:2]]
    except:
        return 'n'  # if mapping isn't found, fall back to Noun.


def find_predict(e1_list, e2_list, source_path, target_path):
    print()
    print(time.strftime("%H:%M:%S", time.localtime()), '========start predict========')
    start = time.perf_counter()

    # source csv
    df_source = pd.DataFrame(e1_list, columns=['Base'])
    e1_list_cleaning = [cleaning(e1) for e1 in e1_list]
    df_source["NT"] = e1_list_cleaning
    e1_list_stopwords = [removing_stop_words(e1) for e1 in e1_list_cleaning]
    df_source["R"] = e1_list_stopwords
    e1_list_sp = [get_stemming(e1, PORTER_STEMMER) for e1 in e1_list_stopwords]
    df_source["SP"] = e1_list_sp
    e1_list_ss = [get_stemming(e1, SNOWBALL_STEMMER) for e1 in e1_list_stopwords]
    df_source["SS"] = e1_list_ss
    e1_list_sl = [get_stemming(e1, LANCASTER_STEMMER) for e1 in e1_list_stopwords]
    df_source["SL"] = e1_list_sl
    e1_list_l = [get_stemming(e1, LEMMATIZER) for e1 in e1_list_stopwords]
    df_source["L"] = e1_list_l
    e1_list_lt = [get_stemming(e1, LEMMATIZER_AND_POS) for e1 in e1_list_stopwords]
    df_source["LT"] = e1_list_lt
    df_source.to_csv(source_path)

    end_source = time.perf_counter()
    duration = end_source - start
    print(time.strftime("%H:%M:%S", time.localtime()), source_path, "save source csv", duration / 60, 'minutes')

    # target csv
    df_target = pd.DataFrame(e2_list, columns=['Base'])
    e2_list_cleaning = [cleaning(e2) for e2 in e2_list]
    df_target["NT"] = e2_list_cleaning
    e2_list_stopwords = [removing_stop_words(e2) for e2 in e2_list_cleaning]
    df_target["R"] = e2_list_stopwords
    e2_list_sp = [get_stemming(e2, PORTER_STEMMER) for e2 in e2_list_stopwords]
    df_target["SP"] = e2_list_sp
    e2_list_ss = [get_stemming(e2, SNOWBALL_STEMMER) for e2 in e2_list_stopwords]
    df_target["SS"] = e2_list_ss
    e2_list_sl = [get_stemming(e2, LANCASTER_STEMMER) for e2 in e2_list_stopwords]
    df_target["SL"] = e2_list_sl
    e2_list_l = [get_stemming(e2, LEMMATIZER) for e2 in e2_list_stopwords]
    df_target["L"] = e2_list_l
    e2_list_lt = [get_stemming(e2, LEMMATIZER_AND_POS) for e2 in e2_list_stopwords]
    df_target["LT"] = e2_list_lt
    df_target.to_csv(target_path)

    end_target = time.perf_counter()
    duration = end_target - end_source
    print(time.strftime("%H:%M:%S", time.localtime()), target_path, "save target csv", duration / 60, 'minutes')

    # add codes for find reserved words

    # predict csv
    find_match(df_source, df_target, y_predict_path_base, BASE)
    find_match(df_source, df_target, y_predict_path_nt, NORMALIZATION_AND_TOKENIZATION)
    find_match(df_source, df_target, y_predict_path_r, REMOVE_STOP_WORDS)
    find_match(df_source, df_target, y_predict_path_sp, PORTER_STEMMER)
    find_match(df_source, df_target, y_predict_path_ss, SNOWBALL_STEMMER)
    find_match(df_source, df_target, y_predict_path_sl, LANCASTER_STEMMER)
    find_match(df_source, df_target, y_predict_path_l, LEMMATIZER)
    find_match(df_source, df_target, y_predict_path_lt, LEMMATIZER_AND_POS)

    end_predict = time.perf_counter()
    duration = end_predict - end_target
    print(time.strftime("%H:%M:%S", time.localtime()), "save predict csv", duration / 60, 'minutes')
    print(time.strftime("%H:%M:%S", time.localtime()), '========finish predict========')
    print()


def find_predict_reserve(e1_list, e2_list, source_path, target_path):
    print()
    print(time.strftime("%H:%M:%S", time.localtime()), '========start predict========')
    start = time.perf_counter()

    # source csv
    df_source = pd.DataFrame(e1_list, columns=['Base'])
    e1_list_cleaning = [cleaning(e1) for e1 in e1_list]
    df_source["NT"] = e1_list_cleaning
    e1_list_stopwords = [removing_stop_words_reserve(e1) for e1 in e1_list_cleaning]
    df_source["R"] = e1_list_stopwords
    e1_list_sp = [get_stemming_reserve(e1, PORTER_STEMMER) for e1 in e1_list_stopwords]
    df_source["SP"] = e1_list_sp
    e1_list_ss = [get_stemming_reserve(e1, SNOWBALL_STEMMER) for e1 in e1_list_stopwords]
    df_source["SS"] = e1_list_ss
    e1_list_sl = [get_stemming_reserve(e1, LANCASTER_STEMMER) for e1 in e1_list_stopwords]
    df_source["SL"] = e1_list_sl
    e1_list_l = [get_stemming_reserve(e1, LEMMATIZER) for e1 in e1_list_stopwords]
    df_source["L"] = e1_list_l
    e1_list_lt = [get_stemming_reserve(e1, LEMMATIZER_AND_POS) for e1 in e1_list_stopwords]
    df_source["LT"] = e1_list_lt
    df_source.to_csv(source_path)

    end_source = time.perf_counter()
    duration = end_source - start
    print(time.strftime("%H:%M:%S", time.localtime()), source_path, "save source csv", duration / 60, 'minutes')

    # target csv
    df_target = pd.DataFrame(e2_list, columns=['Base'])
    e2_list_cleaning = [cleaning(e2) for e2 in e2_list]
    df_target["NT"] = e2_list_cleaning
    e2_list_stopwords = [removing_stop_words_reserve(e2) for e2 in e2_list_cleaning]
    df_target["R"] = e2_list_stopwords
    e2_list_sp = [get_stemming_reserve(e2, PORTER_STEMMER) for e2 in e2_list_stopwords]
    df_target["SP"] = e2_list_sp
    e2_list_ss = [get_stemming_reserve(e2, SNOWBALL_STEMMER) for e2 in e2_list_stopwords]
    df_target["SS"] = e2_list_ss
    e2_list_sl = [get_stemming_reserve(e2, LANCASTER_STEMMER) for e2 in e2_list_stopwords]
    df_target["SL"] = e2_list_sl
    e2_list_l = [get_stemming_reserve(e2, LEMMATIZER) for e2 in e2_list_stopwords]
    df_target["L"] = e2_list_l
    e2_list_lt = [get_stemming_reserve(e2, LEMMATIZER_AND_POS) for e2 in e2_list_stopwords]
    df_target["LT"] = e2_list_lt
    df_target.to_csv(target_path)

    end_target = time.perf_counter()
    duration = end_target - end_source
    print(time.strftime("%H:%M:%S", time.localtime()), target_path, "save target csv", duration / 60, 'minutes')

    # add codes for find reserved words

    # predict csv
    find_match(df_source, df_target, y_predict_path_base, BASE)
    find_match(df_source, df_target, y_predict_path_nt, NORMALIZATION_AND_TOKENIZATION)
    find_match(df_source, df_target, y_predict_path_r, REMOVE_STOP_WORDS)
    find_match(df_source, df_target, y_predict_path_sp, PORTER_STEMMER)
    find_match(df_source, df_target, y_predict_path_ss, SNOWBALL_STEMMER)
    find_match(df_source, df_target, y_predict_path_sl, LANCASTER_STEMMER)
    find_match(df_source, df_target, y_predict_path_l, LEMMATIZER)
    find_match(df_source, df_target, y_predict_path_lt, LEMMATIZER_AND_POS)

    end_predict = time.perf_counter()
    duration = end_predict - end_target
    print(time.strftime("%H:%M:%S", time.localtime()), "save predict csv", duration / 60, 'minutes')
    print(time.strftime("%H:%M:%S", time.localtime()), '========finish predict========')
    print()


# https://github.com/rapidsai/cudf/issues/7521
def find_match(df_source, df_target, y_predict_path, method):
    with open(y_predict_path, "a+", newline='') as f_base:
        writer_base = csv.writer(f_base)
        for i, a in enumerate(df_source[method]):
            for j, b in enumerate(df_target[method]):
                if a == b and a and b:
                    e1 = df_source.iloc[i]['Base']
                    e2 = df_target.iloc[j]['Base']
                    list_pair = [e1, e2]
                    writer_base.writerow(list_pair)


y_predict_path_base = "testbed/predict_base.csv"
y_predict_path_nt = "testbed/predict_nt.csv"
y_predict_path_r = "testbed/predict_r.csv"
y_predict_path_sp = "testbed/predict_sp.csv"
y_predict_path_ss = "testbed/predict_ss.csv"
y_predict_path_sl = "testbed/predict_sl.csv"
y_predict_path_l = "testbed/predict_l.csv"
y_predict_path_lt = "testbed/predict_lt.csv"


def generate_result(folder, e1_list_class, e2_list_class, e1_list_property, e2_list_property):
    source_path_class = folder + "/source_class.csv"
    target_path_class = folder + "/target_class.csv"
    source_path_property = folder + "/source_property.csv"
    target_path_property = folder + "/target_property.csv"
    y_true_path = folder + "/true.csv"
    result_path = folder + "/result.csv"

    # create y_predict file
    create_document(y_predict_path_base, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_nt, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_r, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_sp, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_ss, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_sl, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_l, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_lt, header=['Entity1', 'Entity2'])
    # find predict
    find_predict(e1_list_class, e2_list_class, source_path_class, target_path_class)
    find_predict(e1_list_property, e2_list_property, source_path_property, target_path_property)

    # calculate metrics
    create_document(result_path, header=['Alignment',
                                         'Base-Precision', 'Base-Recall', 'Base-F1',
                                         'NT-Precision', 'NT-Recall', 'NT-F1',
                                         'R-Precision', 'R-Recall', 'R-F1',
                                         'SP-Precision', 'SP-Recall', 'SP-F1',
                                         'SS-Precision', 'SS-Recall', 'SS-F1',
                                         'SL-Precision', 'SL-Recall', 'SL-F1',
                                         'L-Precision', 'L-Recall', 'L-F1',
                                         'LT-Precision', 'LT-Recall', 'LT-F1'])
    with open(result_path, "a+", newline='') as f1:
        writer = csv.writer(f1)
        metrics_base = calculate_metrics(y_true_path, y_predict_path_base)
        metrics_nt = calculate_metrics(y_true_path, y_predict_path_nt)
        metrics_r = calculate_metrics(y_true_path, y_predict_path_r)
        metrics_sp = calculate_metrics(y_true_path, y_predict_path_sp)
        metrics_ss = calculate_metrics(y_true_path, y_predict_path_ss)
        metrics_sl = calculate_metrics(y_true_path, y_predict_path_sl)
        metrics_l = calculate_metrics(y_true_path, y_predict_path_l)
        metrics_lt = calculate_metrics(y_true_path, y_predict_path_lt)
        result = metrics_base + metrics_nt + metrics_r + metrics_sp + metrics_ss + metrics_sl + metrics_l + metrics_lt
        result = [folder] + result
        writer.writerow(result)


def generate_result_reserve(folder, e1_list_class, e2_list_class, e1_list_property, e2_list_property):
    source_path_class = folder + "/source_class.csv"
    target_path_class = folder + "/target_class.csv"
    source_path_property = folder + "/source_property.csv"
    target_path_property = folder + "/target_property.csv"
    y_true_path = folder + "/true.csv"
    result_path_reserve = folder + "/result_reserve.csv"

    # create y_predict file
    create_document(y_predict_path_base, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_nt, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_r, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_sp, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_ss, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_sl, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_l, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_lt, header=['Entity1', 'Entity2'])
    # find predict
    find_predict_reserve(e1_list_class, e2_list_class, source_path_class, target_path_class)
    find_predict_reserve(e1_list_property, e2_list_property, source_path_property, target_path_property)

    # calculate metrics
    create_document(result_path_reserve, header=['Alignment',
                                         'Base-Precision', 'Base-Recall', 'Base-F1',
                                         'NT-Precision', 'NT-Recall', 'NT-F1',
                                         'R-Precision', 'R-Recall', 'R-F1',
                                         'SP-Precision', 'SP-Recall', 'SP-F1',
                                         'SS-Precision', 'SS-Recall', 'SS-F1',
                                         'SL-Precision', 'SL-Recall', 'SL-F1',
                                         'L-Precision', 'L-Recall', 'L-F1',
                                         'LT-Precision', 'LT-Recall', 'LT-F1'])
    with open(result_path_reserve, "a+", newline='') as f1:
        writer = csv.writer(f1)
        metrics_base = calculate_metrics(y_true_path, y_predict_path_base)
        metrics_nt = calculate_metrics(y_true_path, y_predict_path_nt)
        metrics_r = calculate_metrics(y_true_path, y_predict_path_r)
        metrics_sp = calculate_metrics(y_true_path, y_predict_path_sp)
        metrics_ss = calculate_metrics(y_true_path, y_predict_path_ss)
        metrics_sl = calculate_metrics(y_true_path, y_predict_path_sl)
        metrics_l = calculate_metrics(y_true_path, y_predict_path_l)
        metrics_lt = calculate_metrics(y_true_path, y_predict_path_lt)
        result = metrics_base + metrics_nt + metrics_r + metrics_sp + metrics_ss + metrics_sl + metrics_l + metrics_lt
        result = [folder] + result
        writer.writerow(result)


def generate_result_without_alignment(folder, e1_list_class, e2_list_class, e1_list_property, e2_list_property):
    source_path_class = folder + "/source_class.csv"
    target_path_class = folder + "/target_class.csv"
    source_path_property = folder + "/source_property.csv"
    target_path_property = folder + "/target_property.csv"
    # create y_predict file
    create_document(y_predict_path_base, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_nt, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_r, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_sp, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_ss, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_sl, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_l, header=['Entity1', 'Entity2'])
    create_document(y_predict_path_lt, header=['Entity1', 'Entity2'])
    # find predict
    find_predict(e1_list_class, e2_list_class, source_path_class, target_path_class)
    find_predict(e1_list_property, e2_list_property, source_path_property, target_path_property)


def calculate_metrics(true_path, predict_path):
    df_true = pd.read_csv(true_path, encoding="Windows-1250")
    df_predict = pd.read_csv(predict_path, encoding="Windows-1250")
    if df_predict.empty:
        return [0, 0, 0]
    else:
        list_true = df_true.values.tolist()
        list_predict = df_predict.values.tolist()
        common = common_member(list_true, list_predict)
        # print("common", common)
        ra = len(common)
        # print("ra", ra)
        r = len(df_true)
        # print("r", r)
        a = len(df_predict)
        # print("a", a)

        precision = ra / a
        recall = ra / r
        f1 = 2 * (precision * recall) / (precision + recall)
        return ["%.2f" % (precision * 100), "%.2f" % (recall * 100), "%.2f" % (f1 * 100)]


def common_member(a, b):
    result = [i for i in a if i in b]
    return result


def find_reserved_words(df_source_class_path, df_source_property_path,
                        df_target_class_path, df_target_property_path,
                        previous_column, current_column):
    # find source duplicate
    df_source_class = pd.read_csv(df_source_class_path)
    df_source_class = pd.DataFrame(df_source_class, columns=[previous_column, current_column])
    df_source_class_duplicate = df_source_class[df_source_class[current_column].duplicated(keep=False)]
    # print(df_source_class_duplicate)
    df_source_property = pd.read_csv(df_source_property_path)
    df_source_property = pd.DataFrame(df_source_property, columns=[previous_column, current_column])
    df_source_property_duplicate = df_source_property[df_source_property[current_column].duplicated(keep=False)]
    # print(df_source_property_duplicate)
    # find target duplicate
    df_target_class = pd.read_csv(df_target_class_path)
    df_target_class = pd.DataFrame(df_target_class, columns=[previous_column, current_column])
    df_target_class_duplicate = df_target_class[df_target_class[current_column].duplicated(keep=False)]
    # print(df_target_class_duplicate)
    df_target_property = pd.read_csv(df_target_property_path)
    df_target_property = pd.DataFrame(df_target_property, columns=[previous_column, current_column])
    df_target_property_duplicate = df_target_property[df_target_property[current_column].duplicated(keep=False)]
    # print(df_target_property_duplicate)
    # combine all the duplicates
    df_all = pd.concat([df_source_class_duplicate, df_source_property_duplicate,
                        df_target_class_duplicate, df_target_property_duplicate])
    df_all = df_all.drop_duplicates()
    # print(df_all)
    # group items that have the same results
    df_group = pd.DataFrame(df_all.groupby([current_column])[previous_column].apply(list)).reset_index(drop=False)
    # print(df_group)
    # find reserved words
    reserve_set = set()
    df_group_dict = df_group.to_dict('records')
    for row in df_group_dict:
        strs = row[previous_column]
        for i in range(len(strs)):
            for j in range(i + 1, len(strs)):
                # split strings into words
                words_i = set(strs[i].split())
                words_j = set(strs[j].split())
                # find unique words in the pair
                unique_in_pair = words_i.symmetric_difference(words_j)
                # add unique words to the set
                reserve_set.update(unique_in_pair)
    print(reserve_set)
    changed_reserve_set = set()
    # find changed reserved words
    if current_column == REMOVE_STOP_WORDS:
        changed_reserve_set = {word for word in reserve_set if word != removing_stop_words(word)}
    if current_column == PORTER_STEMMER:
        changed_reserve_set = {word for word in reserve_set if word != get_stemming(word, PORTER_STEMMER)}
    if current_column == SNOWBALL_STEMMER:
        changed_reserve_set = {word for word in reserve_set if word != get_stemming(word, SNOWBALL_STEMMER)}
    if current_column == LANCASTER_STEMMER:
        changed_reserve_set = {word for word in reserve_set if word != get_stemming(word, LANCASTER_STEMMER)}
    if current_column == LEMMATIZER:
        changed_reserve_set = {word for word in reserve_set if word != get_stemming(word, LEMMATIZER)}
    if current_column == LEMMATIZER_AND_POS:
        changed_reserve_set = {word for word in reserve_set if word != get_stemming(word, LEMMATIZER_AND_POS)}

    print('changed reserve set', changed_reserve_set)
    return changed_reserve_set


reserved_words_dict = {}


def find_all_reserved_words(df_source_class_path, df_source_property_path,
                            df_target_class_path, df_target_property_path):
    r_reserved_words = find_reserved_words(df_source_class_path, df_source_property_path,
                                           df_target_class_path, df_target_property_path,
                                           NORMALIZATION_AND_TOKENIZATION, REMOVE_STOP_WORDS)
    sp_reserved_words = find_reserved_words(df_source_class_path, df_source_property_path,
                                            df_target_class_path, df_target_property_path,
                                            REMOVE_STOP_WORDS, PORTER_STEMMER)
    ss_reserved_words = find_reserved_words(df_source_class_path, df_source_property_path,
                                            df_target_class_path, df_target_property_path,
                                            REMOVE_STOP_WORDS, SNOWBALL_STEMMER)
    sl_reserved_words = find_reserved_words(df_source_class_path, df_source_property_path,
                                            df_target_class_path, df_target_property_path,
                                            REMOVE_STOP_WORDS, LANCASTER_STEMMER)
    l_reserved_words = find_reserved_words(df_source_class_path, df_source_property_path,
                                           df_target_class_path, df_target_property_path,
                                           REMOVE_STOP_WORDS, LEMMATIZER)
    lt_reserved_words = find_reserved_words(df_source_class_path, df_source_property_path,
                                            df_target_class_path, df_target_property_path,
                                            REMOVE_STOP_WORDS, LEMMATIZER_AND_POS)

    reserved_words_dict[REMOVE_STOP_WORDS] = r_reserved_words
    reserved_words_dict[PORTER_STEMMER] = sp_reserved_words
    reserved_words_dict[SNOWBALL_STEMMER] = ss_reserved_words
    reserved_words_dict[LANCASTER_STEMMER] = sl_reserved_words
    reserved_words_dict[LEMMATIZER] = l_reserved_words
    reserved_words_dict[LEMMATIZER_AND_POS] = lt_reserved_words
    return reserved_words_dict
