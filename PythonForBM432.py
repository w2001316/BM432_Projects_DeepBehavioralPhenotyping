import pandas as pd
import numpy as np
import os, sys, re

# %matplotlib inline

nBPs = 1 # No. of body parts
hN = 8 #
BoxL = 40

hBin = BoxL/hN

def load_prepared_data(path='./ok.csv'):
    # 1. Prepared video info
    data = pd.read_csv(path)
    data = data.set_index('video')
    data['Travel distance (cm)'] = 0
    data['Average speed (cm/min)'] = 0
    data['per_center (%)'] = 0
    return data


def get_video_info(video,data):

    return data.loc[video][:3]


def read_filtered_csv(dir_name, videoname):
    '''
    dir_name: The path to the filtered csv files from DLC
    videoname: String of video name contained in the filtered csv file name

    Return:
        the absolute path of DLC coordinate file for the given video name
    '''
    csv_ls = []
    for root, dirs, files in os.walk(dir_name, topdown=False):
        for filename in files:
            if 'filtered.csv' in filename:
                # print(f'name: {filename}\n, root:{root}\n,')
                csv_ls.append(root + filename)
    try:
        filtered_path = list(filter(lambda x: videoname in x, csv_ls))[0]  # The default file returned is the first one if more than one file exist.
        return filtered_path
    except:
        return (-1)


def process(filtered_path, dur, nBPs=nBPs, start=0):  # The cailbration is process in Jupyter notebook
    T = pd.read_csv(filtered_path)

    T = T.set_index('scorer')
    T = T.drop(['bodyparts', 'coords'])
    # get the number of frames
    fLs = T.index.values.tolist()
    t_reso = dur / len(fLs)  # Unit: min/pixel
    Time = np.arange(t_reso, dur, t_reso)
    # Write into 3D array
    cData = np.zeros((nBPs, len(fLs), 4))
    for i in range(0, nBPs):  # 0/1/2
        MyBid = 3 * (start + i)  # 0/3/6/9/12/15/18/21 : nose/left;right ear/ headcenter/lower/upper/tailroot/tailend
        print(f'Value of i : {i}, Picked body part : {MyBid}')
        cData[i, :, 0] = T.iloc[:, MyBid]  # uncalibrated x coordinate
        # cData[i, :, 0] /= CalX # Convert from pixel distance to acutal distance in cm (CalX unit: pixel/cm)
        cData[i, :, 2] = T.iloc[:, MyBid + 1]  # uncalibrated y coordinate

    return cData, fLs, Time

def cal_speed_acce(cData_co, dur,videoname,data, nBPs = 1):
    fps = int(round(cData_co.shape[1] / dur, 0)) # (# of Sum of frames / Sum of Seconds = Mean fps) round into int
    print(f'fps: {fps}')
    for i in range(nBPs):
        MyX_filtered = np.squeeze(cData_co[i, :, 1])
        MyY_filtered = np.squeeze(cData_co[i, :, 3])
        dist = np.hypot(np.diff(MyX_filtered), np.diff(MyY_filtered))
        bin_num = MyX_filtered.shape[0] // fps
        ls = []
        for bin in range(1,int(bin_num+1)): # the distance per bin (1s) == cm / s
            ls.append(np.sum(dist[fps*(bin-1):fps*bin]))
        ls.append(np.sum(dist[bin_num*fps:]) / (MyX_filtered.shape[0] % fps))

        df = pd.DataFrame(index=range(len(ls)))
        data.loc[videoname, 'Travel distance (cm)'] = np.sum(dist)
        # df['Speed'] = df['Distance'] / (1 / fps)
        df['Speed(cm/s)'] = ls
        df['Acceleration(cm/s^(2))'] = df['Speed(cm/s)'].diff().abs()
        data.loc[videoname, 'Average speed (cm/min)'] = np.mean(df['Acceleration(cm/s^(2))'])
    return df


    # videoinfo = pd.read_csv('/Users/arthur/Behavior/ok.csv')
    # videoinfo = videoinfo.set_index('video')


def edge_prefer(fLs,cData ,videoname,data, EdgeWidth=5, BoxL=BoxL):  # Better to calculate by using nose
    MyBP = 1
    BoxSize = BoxL
    MyXY = np.squeeze(cData[MyBP - 1, :, 1:4:2])
    # MyXY.shape
    MyXY = MyXY.tolist()
    NumFrame = np.squeeze(cData[MyBP - 1, :, 1:4:2]).shape[0]
    # Sum and get the proporation of a mouse in the central arena
    ls_center = []
    for i in range(NumFrame):
        if MyXY[i][0] >= EdgeWidth and MyXY[i][0] <= (BoxSize - EdgeWidth) and MyXY[i][1] >= EdgeWidth and MyXY[i][
            1] <= (BoxSize - EdgeWidth):
            ls_center.append(i)

    per_center_val = len(ls_center) / len(fLs)
    data.loc[videoname, 'per_center (%)'] = per_center_val
    return data


