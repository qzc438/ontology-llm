import util
import pandas as pd
import csv
import om_ontology_to_csv


def generate_results_2022(folder, alignment_name):
    util.calculate_benchmark_metrics(folder + "/true.csv", folder + "/predict.csv",
                                     "benchmark_2022/conference/conference-result.csv",
                                     alignment_name)


def generate_results_2023(folder, alignment_name):
    util.calculate_benchmark_metrics(folder + "/true.csv", folder + "/predict.csv",
                                     "benchmark_2023/conference/conference-result.csv",
                                     alignment_name)


def generate_results_dbpedia(folder, alignment_name):
    util.calculate_benchmark_metrics(folder + "/true.csv", folder + "/predict.csv",
                                     "benchmark_2022/conference/dbpedia-result.csv",
                                     alignment_name)


if __name__ == '__main__':

    # 2022 results
    util.create_document("benchmark_2022/conference/conference-result.csv",
                         header=['Name', 'Precision', 'Recall', 'F1'])
    generate_results_2022("alignment/conference/cmt-conference/component", "cmt-conference")
    generate_results_2022("alignment/conference/cmt-confof/component", "cmt-confof")
    generate_results_2022("alignment/conference/cmt-edas/component", "cmt-edas")
    generate_results_2022("alignment/conference/cmt-ekaw/component", "cmt-ekaw")
    generate_results_2022("alignment/conference/cmt-iasted/component", "cmt-iasted")
    generate_results_2022("alignment/conference/cmt-sigkdd/component", "cmt-sigkdd")
    generate_results_2022("alignment/conference/conference-confof/component", "conference-confof")
    generate_results_2022("alignment/conference/conference-edas/component", "conference-edas")
    generate_results_2022("alignment/conference/conference-ekaw/component", "conference-ekaw")
    generate_results_2022("alignment/conference/conference-iasted/component", "conference-iasted")
    generate_results_2022("alignment/conference/conference-sigkdd/component", "conference-sigkdd")
    generate_results_2022("alignment/conference/confof-edas/component", "confof-edas")
    generate_results_2022("alignment/conference/confof-ekaw/component", "confof-ekaw")
    generate_results_2022("alignment/conference/confof-iasted/component", "confof-iasted")
    generate_results_2022("alignment/conference/confof-sigkdd/component", "confof-sigkdd")
    generate_results_2022("alignment/conference/edas-ekaw/component", "edas-ekaw")
    generate_results_2022("alignment/conference/edas-iasted/component", "edas-iasted")
    generate_results_2022("alignment/conference/edas-sigkdd/component", "edas-sigkdd")
    generate_results_2022("alignment/conference/ekaw-iasted/component", "ekaw-iasted")
    generate_results_2022("alignment/conference/ekaw-sigkdd/component", "ekaw-sigkdd")
    generate_results_2022("alignment/conference/iasted-sigkdd/component", "iasted-sigkdd")

    df = pd.read_csv('benchmark_2022/conference/conference-result.csv')
    average_precision = df['Precision'].mean()
    average_recall = df['Recall'].mean()
    average_f1 = df['F1'].mean()
    print(f"{average_precision:.2f}", f"{average_recall:.2f}", f"{average_f1:.2f}")

    benchmark_file = 'benchmark_2022/conference/conference_benchmark.csv'
    # initialize an empty list to hold rows that don't match the search_name
    rows_to_keep = []
    with open(benchmark_file, mode='r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] != "Agent-OM":
                # only add rows that don't match the search_name
                rows_to_keep.append(row)
    # write the rows that don't match the search_name back to the CSV file
    with open(benchmark_file, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows_to_keep[0].keys())
        writer.writeheader()
        writer.writerows(rows_to_keep)
    # add Agent-OM results into the benchmark
    with open(benchmark_file, "a+", newline='') as f:
        writer = csv.writer(f)
        result = ["%.2f" % (average_precision), "%.2f" % (average_recall), "%.2f" % (average_f1)]
        result = ["Agent-OM"] + result
        writer.writerow(result)

    # 2023 results
    util.create_document("benchmark_2023/conference/conference-result.csv",
                         header=['Name', 'Precision', 'Recall', 'F1'])
    generate_results_2023("alignment/conference/cmt-conference/component", "cmt-conference")
    generate_results_2023("alignment/conference/cmt-confof/component", "cmt-confof")
    generate_results_2023("alignment/conference/cmt-edas/component", "cmt-edas")
    generate_results_2023("alignment/conference/cmt-ekaw/component", "cmt-ekaw")
    generate_results_2023("alignment/conference/cmt-iasted/component", "cmt-iasted")
    generate_results_2023("alignment/conference/cmt-sigkdd/component", "cmt-sigkdd")
    generate_results_2023("alignment/conference/conference-confof/component", "conference-confof")
    generate_results_2023("alignment/conference/conference-edas/component", "conference-edas")
    generate_results_2023("alignment/conference/conference-ekaw/component", "conference-ekaw")
    generate_results_2023("alignment/conference/conference-iasted/component", "conference-iasted")
    generate_results_2023("alignment/conference/conference-sigkdd/component", "conference-sigkdd")
    generate_results_2023("alignment/conference/confof-edas/component", "confof-edas")
    generate_results_2023("alignment/conference/confof-ekaw/component", "confof-ekaw")
    generate_results_2023("alignment/conference/confof-iasted/component", "confof-iasted")
    generate_results_2023("alignment/conference/confof-sigkdd/component", "confof-sigkdd")
    generate_results_2023("alignment/conference/edas-ekaw/component", "edas-ekaw")
    generate_results_2023("alignment/conference/edas-iasted/component", "edas-iasted")
    generate_results_2023("alignment/conference/edas-sigkdd/component", "edas-sigkdd")
    generate_results_2023("alignment/conference/ekaw-iasted/component", "ekaw-iasted")
    generate_results_2023("alignment/conference/ekaw-sigkdd/component", "ekaw-sigkdd")
    generate_results_2023("alignment/conference/iasted-sigkdd/component", "iasted-sigkdd")

    df = pd.read_csv('benchmark_2023/conference/conference-result.csv')
    average_precision = df['Precision'].mean()
    average_recall = df['Recall'].mean()
    average_f1 = df['F1'].mean()
    print(f"{average_precision:.2f}", f"{average_recall:.2f}", f"{average_f1:.2f}")

    benchmark_file = 'benchmark_2023/conference/conference_benchmark.csv'
    # initialize an empty list to hold rows that don't match the search_name
    rows_to_keep = []
    with open(benchmark_file, mode='r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] != "Agent-OM":
                # only add rows that don't match the search_name
                rows_to_keep.append(row)
    # write the rows that don't match the search_name back to the CSV file
    with open(benchmark_file, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows_to_keep[0].keys())
        writer.writeheader()
        writer.writerows(rows_to_keep)
    # add Agent-OM results into the benchmark
    with open(benchmark_file, "a+", newline='') as f:
        writer = csv.writer(f)
        result = ["%.2f" % (average_precision), "%.2f" % (average_recall), "%.2f" % (average_f1)]
        result = ["Agent-OM"] + result
        writer.writerow(result)

    # # dbpedia result is not included in the paper because we cannot find OAEI 2023 benchmarks
    # om_ontology_to_csv.find_reference("data/conference/dbpedia-confof/component/reference.xml",
    #                                   "alignment/conference/dbpedia-confof/component/true.csv")
    # om_ontology_to_csv.find_reference("data/conference/dbpedia-ekaw/component/reference.xml",
    #                                   "alignment/conference/dbpedia-ekaw/component/true.csv")
    # om_ontology_to_csv.find_reference("data/conference/dbpedia-sigkdd/component/reference.xml",
    #                                   "alignment/conference/dbpedia-sigkdd/component/true.csv")
    # util.create_document("benchmark_2022/conference/dbpedia-result.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    # generate_results_dbpedia("alignment/conference/dbpedia-confof/component", "dbpedia-confof")
    # generate_results_dbpedia("alignment/conference/dbpedia-ekaw/component", "dbpedia-ekaw")
    # generate_results_dbpedia("alignment/conference/dbpedia-sigkdd/component", "dbpedia-sigkdd")
    # df = pd.read_csv('benchmark_2022/conference/dbpedia-result.csv')
    # average_precision = df['Precision'].mean()
    # average_recall = df['Recall'].mean()
    # average_f1 = df['F1'].mean()
    # print(f"{average_precision:.2f}", f"{average_recall:.2f}", f"{average_f1:.2f}")
