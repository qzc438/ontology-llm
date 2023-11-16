import pandas as pd
import util


def generate_filtered_csv(input_path, output_path):
    df = pd.read_csv(input_path)

    delimiter = ':'
    df['Entity1_Normal'] = df['Entity1'].str.split(delimiter).str.get(-1)
    df['Entity2_Normal'] = df['Entity2'].str.split(delimiter).str.get(-1)

    df['Entity1_Normal'] = df['Entity1_Normal'].apply(util.cleaning)
    df['Entity2_Normal'] = df['Entity2_Normal'].apply(util.cleaning)

    condition = df['Entity1_Normal'] != df['Entity2_Normal']
    filtered_df = df[condition]
    filtered_df = filtered_df.drop(columns=['Entity1_Normal', 'Entity2_Normal'])

    filtered_df.to_csv(output_path, index=False)


if __name__ == '__main__':

    # df_source = pd.read_csv('alignment/conference/cmt-conference/component/predict_source.csv')
    # df_target = pd.read_csv('alignment/conference/cmt-conference/component/predict_target.csv')
    # df_common = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # df_common.to_csv("alignment/conference/cmt-conference/component/predict.csv", index=False)
    # util.calculate_metrics('alignment/conference/cmt-conference/component/true.csv',
    #                        'alignment/conference/cmt-conference/component/predict.csv',
    #                        'conference_merge', 'result.csv')

    # df_source = pd.read_csv('alignment/anatomy/mouse-human-suite/component/predict_source.csv')
    # df_target = pd.read_csv('alignment/anatomy/mouse-human-suite/component/predict_target.csv')
    # df_common = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # df_common.to_csv("alignment/anatomy/mouse-human-suite/component/predict.csv", index=False)
    # util.calculate_metrics('alignment/anatomy/mouse-human-suite/component/true.csv',
    #                        'alignment/anatomy/mouse-human-suite/component/predict.csv',
    #                        'anatomy_merge', 'result.csv')

    # generate_filtered_csv('alignment/anatomy/mouse-human-suite/component/true.csv',
    #                       'alignment/anatomy/mouse-human-suite/component/true_filtered.csv')
    # generate_filtered_csv('alignment/anatomy/mouse-human-suite/component/predict.csv',
    #                       'alignment/anatomy/mouse-human-suite/component/predict_filtered.csv')
    # util.calculate_metrics('alignment/anatomy/mouse-human-suite/component/true_filtered.csv',
    #                        'alignment/anatomy/mouse-human-suite/component/predict_filtered.csv',
    #                        'anatomy_filter', 'result.csv')

    # mask = df1['Entity1'].isin(df2['Entity1'])
    # result_df = df1[~mask]
    # print(result_df)

    # df_source = pd.read_csv('alignment/conference/cmt-conference/component/predict_source.csv')
    # df_target = pd.read_csv('alignment/conference/cmt-conference/component/predict_target.csv')
    # df_common = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # df_common.to_csv("alignment/conference/cmt-conference/component/predict.csv", index=False)
    # util.calculate_metrics('alignment/conference/cmt-conference/component/true.csv',
    #                        'alignment/conference/cmt-conference/component/predict.csv',
    #                        'alignment/conference/cmt-conference/', 'result.csv')

    # df_source = pd.read_csv('alignment/conference/cmt-confof/component/predict_source.csv')
    # df_target = pd.read_csv('alignment/conference/cmt-confof/component/predict_target.csv')
    # df_common = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # df_common.to_csv("alignment/conference/cmt-confof/component/predict.csv", index=False)
    # util.calculate_metrics('alignment/conference/cmt-confof/component/true.csv',
    #                        'alignment/conference/cmt-confof/component/predict.csv',
    #                        'alignment/conference/cmt-confof/', 'result.csv')

    # df_source = pd.read_csv('alignment/conference/cmt-edas/component/predict_source.csv')
    # df_target = pd.read_csv('alignment/conference/cmt-edas/component/predict_target.csv')
    # df_common = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # df_common.to_csv("alignment/conference/cmt-edas/component/predict.csv", index=False)
    # util.calculate_metrics('alignment/conference/cmt-edas/component/true.csv',
    #                        'alignment/conference/cmt-edas/component/predict.csv',
    #                        'alignment/conference/cmt-edas/', 'result.csv')

    # df_source = pd.read_csv('alignment/conference/cmt-ekaw/component/predict_source.csv')
    # df_target = pd.read_csv('alignment/conference/cmt-ekaw/component/predict_target.csv')
    # df_common = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # df_common.to_csv("alignment/conference/cmt-ekaw/component/predict.csv", index=False)
    # util.calculate_metrics('alignment/conference/cmt-ekaw/component/true.csv',
    #                        'alignment/conference/cmt-ekaw/component/predict.csv',
    #                        'alignment/conference/cmt-ekaw/', 'result.csv')

    # df_source = pd.read_csv('alignment/conference/cmt-ekaw/component/predict_source.csv')
    # df_target = pd.read_csv('alignment/conference/cmt-ekaw/component/predict_target.csv')
    # df_common = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # df_common.to_csv("alignment/conference/cmt-ekaw/component/predict.csv", index=False)
    # util.calculate_metrics('alignment/conference/cmt-ekaw/component/true.csv',
    #                        'alignment/conference/cmt-ekaw/component/predict.csv',
    #                        'alignment/conference/cmt-ekaw/', 'result.csv')

    df_source = pd.read_csv('alignment/conference/cmt-iasted/component/predict_source.csv')
    df_target = pd.read_csv('alignment/conference/cmt-iasted/component/predict_target.csv')
    df_common = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    df_common.to_csv("alignment/conference/cmt-iasted/component/predict.csv", index=False)
    util.calculate_metrics('alignment/conference/cmt-iasted/component/true.csv',
                           'alignment/conference/cmt-iasted/component/predict.csv',
                           'alignment/conference/cmt-iasted/', 'result.csv')