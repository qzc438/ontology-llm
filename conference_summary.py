import util
import pandas as pd
import om_ontology_to_csv


def generate_results(folder, alignment_name):
    util.calculate_metrics(folder + "/true.csv", folder + "/predict.csv", alignment_name, "conference-result.csv")


def generate_results_dbpedia(folder, alignment_name):
    util.calculate_metrics(folder + "/true.csv", folder + "/predict.csv", alignment_name, "dbpedia-result.csv")


if __name__ == '__main__':
    util.create_document("conference-result.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    generate_results("alignment/conference/cmt-conference/component", "cmt-conference")
    generate_results("alignment/conference/cmt-confof/component", "cmt-confof")
    generate_results("alignment/conference/cmt-edas/component", "cmt-edas")
    generate_results("alignment/conference/cmt-ekaw/component", "cmt-ekaw")
    generate_results("alignment/conference/cmt-iasted/component", "cmt-iasted")
    generate_results("alignment/conference/cmt-sigkdd/component", "cmt-sigkdd")

    generate_results("alignment/conference/conference-confof/component", "conference-confof")
    generate_results("alignment/conference/conference-edas/component", "conference-edas")
    generate_results("alignment/conference/conference-ekaw/component", "conference-ekaw")
    generate_results("alignment/conference/conference-iasted/component", "conference-iasted")
    generate_results("alignment/conference/conference-sigkdd/component", "conference-sigkdd")

    generate_results("alignment/conference/confof-edas/component", "confof-edas")
    generate_results("alignment/conference/confof-ekaw/component", "confof-ekaw")
    generate_results("alignment/conference/confof-iasted/component", "confof-iasted")
    generate_results("alignment/conference/confof-sigkdd/component", "confof-sigkdd")

    generate_results("alignment/conference/edas-ekaw/component", "edas-ekaw")
    generate_results("alignment/conference/edas-iasted/component", "edas-iasted")
    generate_results("alignment/conference/edas-sigkdd/component", "edas-sigkdd")

    generate_results("alignment/conference/ekaw-iasted/component", "ekaw-iasted")
    generate_results("alignment/conference/ekaw-sigkdd/component", "ekaw-sigkdd")

    generate_results("alignment/conference/iasted-sigkdd/component", "iasted-sigkdd")

    df = pd.read_csv('conference-result.csv')
    average_precision = df['Precision'].mean()
    average_recall = df['Recall'].mean()
    average_f1 = df['F1'].mean()
    print(average_precision, average_recall, average_f1)

    om_ontology_to_csv.find_alignment("data/conference/dbpedia-confof/component/reference.xml",
                                      "alignment/conference/dbpedia-confof/component/true.csv")
    om_ontology_to_csv.find_alignment("data/conference/dbpedia-ekaw/component/reference.xml",
                                      "alignment/conference/dbpedia-ekaw/component/true.csv")
    om_ontology_to_csv.find_alignment("data/conference/dbpedia-sigkdd/component/reference.xml",
                                      "alignment/conference/dbpedia-sigkdd/component/true.csv")

    util.create_document("dbpedia-result.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    generate_results_dbpedia("alignment/conference/dbpedia-confof/component", "dbpedia-confof")
    generate_results_dbpedia("alignment/conference/dbpedia-ekaw/component", "dbpedia-ekaw")
    generate_results_dbpedia("alignment/conference/dbpedia-sigkdd/component", "dbpedia-sigkdd")

    df = pd.read_csv('dbpedia-result.csv')
    average_precision = df['Precision'].mean()
    average_recall = df['Recall'].mean()
    average_f1 = df['F1'].mean()
    print(average_precision, average_recall, average_f1)
