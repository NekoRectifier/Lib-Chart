import json
import time

import pandas as pd
import requests
import schedule

# CONSTS
userId = "202104030"
userPwd = userId

# TIME RELATED
TARGET_DATE = time.strftime("%Y-%m-%d", time.localtime())

BEGIN = TARGET_DATE + ' 08:30:00'
END = TARGET_DATE + '22:00:00'

# ------------------------------------------

headers = {
    'Referer': 'https://zwyy.qdexam.com/www/login.html',
    'Origin': 'https://zwyy.qdexam.com',
    'Host': 'zwyy.qdexam.com',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': '*/*',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache'
}

headers2 = {
    'Referer': 'https://zwyy.qdexam.com/www/subscribe.html',
    'Origin': 'https://zwyy.qdexam.com',
    'Connection': 'keep-alive'
}

headers3 = {
    'Referer': 'https://zwyy.qdexam.com/www/optionalSeat.html?_r=0.30982000108995643',
    'Origin': 'https://zwyy.qdexam.com',
    'Connection': 'keep-alive'
}

s = ''
userInfoId = ''


def init():
    """
    Do some necessary jobs
    :return: nothing
    """
    global s, userInfoId
    s = requests.session()

    login = s.post(
        "https://zwyy.qdexam.com/userInfo/login",
        data={'userNum': userId, 'userPwd': userPwd, 'schoolNum': '3df715dc-e177-4b71-907c-af530ff9f8ca'},
        headers=headers)

    userInfoId = json.loads(login.text)["object"]["userInfoId"]
    print("userIId", userInfoId)

    # building_detail = s.post(
    #     "https://zwyy.qdexam.com/selectInfo/selectCampusAndBuildingInfomation",
    #     data={'userInfoId': userInfoId},
    #     headers=headers2
    # )
    # existingBuildingIds = []
    # for i in json.loads(building_detail.text)['list']:
    #     existingBuildingIds.append(i.get('buildingId'))
    # print(existingBuildingIds)
    # Here is the list of all available building in your university,

    # room_detail = s.post( "https://zwyy.qdexam.com/selectInfo/selectEachClassroom", data={'buildingId':
    # existingBuildingIds[ 0]}, headers=headers2 # might be some useful info in there # # {"success":true,
    # "message":null,"object":null, "list":[{"total":125,"classroomNum":"四自修室","seatState":0,"fixedBeginDate":null,
    # "campusId":20,"classroomId":154, "fixedEndDate":null,"fixedReservationTime":null,"floor":4,"buildingId":13},
    # {"total":150,"classroomNum":"五自修室", "seatState":0,"fixedBeginDate":null,"campusId":20,"classroomId":113,
    # "fixedEndDate":null, "fixedReservationTime":null,"floor":5,"buildingId":13}],"listString":null,"lists":null,
    # "sumReservation":null, "sumBlackListCount":null,"sumComplaintListCount":null,"version":null,"url":null,
    # "token":null,"userCount":null, "recommendList":null} )
    #
    # print(room_detail.text)


def get_seats_data(room_id, begin_time="08:30:00", end_time="22:00:00"):
    """
    Get data of every seat in the specific room
    :param room_id: 4th floor is 154; 5th floor is 113. Different university have respective values
    :param begin_time: the time you want to reserve, DOES NOT have effect on other reservation
    :param end_time: same above
    :return: parsed "list" data of seat
    """
    # TODO multi-room possibility
    room = s.post(
        "https://zwyy.qdexam.com/selectInfo/selectEachClassroom_SeatsInfo",
        data={
            'classroomId': room_id,
            'reservationBeginTime': TARGET_DATE + ' ' + begin_time,
            'reservationEndTime': TARGET_DATE + ' ' + end_time
        }
    )
    return json.loads(room.text)['object']['seatList']


# this func is deprecated
def data_processing(lists):
    """
    Mark out different status of each seat
    :param lists:
    :return: occupied seat data with its occupation type
    """
    occupied_seats = []

    for seats_data in lists:
        for seat in seats_data:
            state = seat.get('state')
            readable_pos = seat.get('seatNum')
            if state == 3:
                # full occupied state
                occupied_seats.append(seat)
                print("FULL-OCC", readable_pos)
            elif state == 2:
                # partly occupied state
                occupied_seats.append(seat)
                print("PART-OCC", readable_pos)
            elif state == 1:
                print("##-EMPTY", readable_pos)
            else:
                print("Unknown Status:", readable_pos)

    print(occupied_seats)
    return occupied_seats


def improv_data_process(lists):
    obj_list = []
    for seats_data in lists:
        for seat in seats_data:
            obj_list.append(seat)
    return obj_list


def get_reserve_time(seat_id):
    seat_data = s.post(
        "https://zwyy.qdexam.com/reservation/selectReservationByInspect",
        data={
            'userInfoId': userInfoId,
            'seatId': seat_id
        }
    )
    _list = json.loads(seat_data.text).get('list')

    for _list_obj in _list:
        # TODO multi-day support
        print('')

    res_begin = _list[0]['reservationBeginTime']
    res_end = _list[0]['reservationEndTime']
    # print("RES", res_begin, res_end)

    if res_begin is not None and res_end is not None:
        return res_begin, res_end
    else:
        raise AttributeError


def save_data(processed_data, name):
    df = pd.DataFrame(processed_data)
    df.set_index('seatNum')
    df.to_csv(name + '.csv')


def complete_reservation_detail(seats):
    """
    Add time information of reservation, and save the data into csv file
    :param seats:
    :return:
    """
    _begin, _end = '', ''
    curr_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    for seat in seats:
        # print('inspecting id: ' + seat['seatNum'] + '\n' + seat)

        state = seat.get('state', -1)

        if state == 2:
            _begin, _end = get_reserve_time(seat['seatId'])
        elif state == 3:
            _begin = BEGIN
            _end = END
        elif state == 1:
            _begin, _end = '', ''

        seat['begin'] = _begin
        seat['end'] = _end
        seat['catch_time'] = curr_time
    save_data(seats, curr_time)


def run_once():
    lists_data = [get_seats_data(154), get_seats_data(113)]
    occu_seats = improv_data_process(lists_data)
    complete_reservation_detail(occu_seats)

    # TODO status report


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    """ This program is designed to run at all times, do not stop it unless enough data is collected.
    """
    init()
    run_once()

    schedule.every(15).minutes.do(run_once)
    while True:
        schedule.run_pending()
        time.sleep(1)
