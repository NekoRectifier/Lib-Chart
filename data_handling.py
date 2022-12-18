
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# CONSTS
LABELS = ['Unnamed', 'userSex', 'userNum', 'columnNum', 'classroomId', 'notArrive', 'seatRows', 'seatNum',
          'classroomNum', 'rowNum', 'seatColumns', 'seatId', 'state', 'leaveFlag', 'begin', 'end', 'catch_time']

# used to separate different room in func pre_process
SEAT_NUM_4 = 125
SEAT_NUM_5 = 150


def merge_csv(csv_files_path: str):
    """
    Merge all csv file for further process
    :param csv_files_path:
    :return: Pandas.DataFrame ready to use
    """
    fd_list = []

    print('merging...')
    for root, dirs, files in os.walk(csv_files_path, topdown=True):
        for file in files:
            if str(file).endswith(".csv"):
                fd_list.append(
                    pd.read_csv(os.path.join(root, file), index_col=0, header=0))

    if len(fd_list) == 0:
        print('No existing ".csv" files found')
        raise FileNotFoundError
    return pd.concat(fd_list, ignore_index=True)


def pre_process(df_handle: pd.DataFrame):
    """
    Split the data into each room group
    :return: tuple that contains processed data
    """
    df_4: pd.DataFrame = pd.DataFrame(columns=LABELS)
    df_5: pd.DataFrame = pd.DataFrame(columns=LABELS)

    print('handle', len(df_handle))
    merged_file_num = int(len(df_handle) / 275)

    # for index in range(0, len(df_handle)):
    #     row = df_handle.loc[index]
    #     # TODO bypass unnecessary items, how?
    #     # seats amount is fixed, why do i need to separate them manually?
    #     if row['classroomId'] == 154:
    #         # 4th floor
    #         df_1 = df_1.append(row)
    #         # df_1 = pd.concat([row, df_1], axis=0)
    #     elif row['classroomId'] == 113:
    #         # 5th floor
    #         # df_2 = pd.concat([row, df_2], axis=0)
    #         df_2 = df_2.append(row)
    #     else:
    #         print('no')

    for index in range(0, merged_file_num):
        offset = index * (SEAT_NUM_5 + SEAT_NUM_4)

        df_4 = pd.concat(
            [df_4,
             df_handle.iloc[offset: SEAT_NUM_4 + offset]]
        )

        df_5 = pd.concat(
            [df_5,
             df_handle.iloc[SEAT_NUM_4 + offset: SEAT_NUM_4 + SEAT_NUM_5 + offset]]
        )
    return df_4, df_5


def gen_heat_matrix(data, floor_num=4):
    """
    Extract the "heat" data into a matrix
    :param floor_num:
    :param data: original data
    :return: heat matrix with size of max rowNum and columnNum
    """

    if floor_num == 4:  # 24, 11
        mat = np.zeros((25, 12))
    elif floor_num == 5:  # 29, 10
        mat = np.zeros((30, 11))
    else:
        print("No Correspond Floor Exist")
        raise AttributeError

    for row_index in range(0, len(data)):
        row = data.iloc[row_index]

        if row['seatId'] == 'nan':
            continue

        _y = row['columnNum'] - 1
        _x = row['rowNum'] - 1
        # print('x:', _x, '_y', _y)

        if row['state'] == 2 or row['state'] == 3:
            # the Num in data has offsets
            mat[_x][_y] = mat[_x][_y] + 0.8
        else:
            mat[_x][_y] = 0.4

    print(mat)
    return mat


if __name__ == "__main__":
    full_csv = merge_csv('.')

    d4, d5 = pre_process(full_csv)
    heatmap_4 = sns.heatmap(
        gen_heat_matrix(d4, 4),
        vmin=0,
        cmap="Greys",
        linewidths=0.1
    )

    plt.show()

    heatmap_5 = sns.heatmap(
        gen_heat_matrix(d5, 5),
        vmin=0,
        cmap="Greys",
        linewidths=0.1
    )

    plt.show()
