import os
import csv
import re
import enchant
import rdflib
import pandas as pd


def find_uri(ontology):
    for ns_prefix, namespace in ontology.namespaces():
        if not ns_prefix:
            return namespace
    return ""


def uri_to_prefix_name(uri, prefix):
    uri_str = str(uri)
    if "#" in uri_str:
        return prefix + ":" + str(uri).split("#")[-1]
    else:
        return prefix + ":" + str(uri).split("/")[-1]


def uri_to_name(uri):
    uri_str = str(uri)
    if "#" in uri_str:
        return uri_str.split("#")[-1]
    else:
        return uri_str.split("/")[-1]


def prefix_name_to_name(prefix_name):
    return prefix_name.split(":")[-1]


def name_to_prefix_name(name, prefix):
    return prefix + ":" + str(name.replace("'", ""))


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
    # name = name.lower()
    # name = change_british_to_american(name)
    # capitalized_name = ' '.join(word.capitalize() for word in name.split())
    return name


def calculate_metrics(true_path, predict_path, alignment, result_path):
    df_true = pd.read_csv(true_path, encoding="Windows-1250")
    df_predict = pd.read_csv(predict_path, encoding="Windows-1250")
    if df_predict.empty:
        return [0, 0, 0]
    else:
        # list_true = df_true.values.tolist()
        # list_predict = df_predict.values.tolist()
        # common = common_member(list_true, list_predict)
        common = pd.merge(df_true, df_predict, on=['Entity1', 'Entity2'], how="inner")
        # remove any duplicate rows in the common
        common = common.drop_duplicates()
        # print(common)
        ra = len(common)
        print("ra:", ra)
        if ra == 0:
            return [0, 0, 0]
        else:
            r = len(df_true)
            print("r:", r)
            a = len(df_predict)
            print("a:", a)
            precision = ra / a
            recall = ra / r
            f1 = 2 * (precision * recall) / (precision + recall)
            # write to file
            # create_document(result_path, header=['Alignment', 'Precision', 'Recall', 'F1'])
            with open(result_path, "a+", newline='') as f:
                writer = csv.writer(f)
                result = ["%.2f" % (precision * 100), "%.2f" % (recall * 100), "%.2f" % (f1 * 100)]
                result = [alignment] + result
                writer.writerow(result)
            # print results
            return ["%.2f" % (precision * 100), "%.2f" % (recall * 100), "%.2f" % (f1 * 100)]


def common_member(a, b):
    result = [i for i in a if i in b]
    return result


if __name__ == '__main__':
    # calculate_metrics("alignment/mse/MaterialInformation-EMMO/component/true.csv",
    #                   "alignment/mse/MaterialInformation-EMMO/component/predict_no_validation.csv",
    #                   "", "")

    df1 = pd.read_csv("benchmark_2022/mse/thirdTestCase/LogMap.csv")
    df2 = pd.read_csv("alignment/mse/MaterialInformation-EMMO/component/predict.csv")

    result_df = pd.merge(df1, df2, on=["Entity1", "Entity2"], how="inner")
    # remove any duplicate rows in the resulting DataFrame
    result_df = result_df.drop_duplicates()
    print(len(result_df))
    result_df.to_csv('test_function.csv', index=False)

    # use an outer join with an indicator to find differences
    diff_df = pd.merge(df1, df2, on=["Entity1", "Entity2"], how='outer', indicator=True)
    # filter rows that are either only in df1 or only in df2
    diff_df1_only = diff_df[diff_df['_merge'] == 'left_only']
    diff_df2_only = diff_df[diff_df['_merge'] == 'right_only']
    # show the differences
    print("Rows in df1 not in df2:")
    print(diff_df1_only)
    print("Rows in df2 not in df1:")
    print(diff_df2_only)

    # test cleaning
    print(cleaning("Al"))


