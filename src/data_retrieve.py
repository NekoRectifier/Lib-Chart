import json
import time
import pandas as pd
import requests

# CONSTS
userId = "202104030"
userPwd = userId

# TIME RELATED
date: str
TIME_BEGIN = "08:30:00"
TIME_END = "22:00:00"

# flags
login_status = False

headers = {
    "Referer": "https://zwyy.qdexam.com/www/login.html",
    "Origin": "https://zwyy.qdexam.com",
    "Host": "zwyy.qdexam.com",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
}

headers2 = {
    "Referer": "https://zwyy.qdexam.com/www/subscribe.html",
    "Origin": "https://zwyy.qdexam.com",
    "Connection": "keep-alive",
}

headers3 = {
    "Referer": "https://zwyy.qdexam.com/www/optionalSeat.html?_r=0.30982000108995643",
    "Origin": "https://zwyy.qdexam.com",
    "Connection": "keep-alive",
}

s = requests.session()
userInfoId = ""


def init():
    """
    Do some necessary jobs
    :return: nothing
    """
    global s, userInfoId, date, login_status

    date = time.strftime("%Y-%m-%d", time.localtime())
    login = s.post(
        "https://zwyy.qdexam.com/userInfo/login",
        data={
            "userNum": userId,
            "userPwd": userPwd,
            "schoolNum": "3df715dc-e177-4b71-907c-af530ff9f8ca",  # HUAT
        },
        headers=headers,
    )

    _json_body = json.loads(login.text)

    print(login.text)
    # print(_json_body["success"])

    if _json_body["success"]:
        userInfoId = _json_body["object"]["userInfoId"]
        print(
            "login successful \nuserId:",
            userInfoId,
            "Name:",
            _json_body["object"]["userName"],
            "SeatComplaint:",
            _json_body["object"]["seatComplaint"],
            "\nSex:",
            _json_body["object"]["userSex"],
            "Entry Year:",
            _json_body["object"]["studentYear"]
        )
        login_status = True
    else:
        print("user login failed")
        exit(1)


def get_seats_data(room_id, begin_time="08:30:00", end_time="22:00:00"):
    """
    Get data of every seat in the specific room
    :param room_id: 4th floor is 154; 5th floor is 113. Different university have respective values
    :param begin_time: the time you want to reserve, DOES NOT have effect on other reservation
    :param end_time: same above
    :return: parsed "list" data of seat
    """

    room = s.post(
        "https://zwyy.qdexam.com/selectInfo/selectEachClassroom_SeatsInfo",
        data={
            "classroomId": room_id,
            "reservationBeginTime": date + " " + begin_time,
            "reservationEndTime": date + " " + end_time,
        },
    )
    return json.loads(room.text)["object"]["seatList"]


def get_reserve_time(seat_id):
    seat_data = s.post(
        "https://zwyy.qdexam.com/reservation/selectReservationByInspect",
        data={"userInfoId": userInfoId, "seatId": seat_id},
    )
    _list = json.loads(seat_data.text).get("list")

    res_begin = _list[0]["reservationBeginTime"]
    res_end = _list[0]["reservationEndTime"]

    if res_begin is not None and res_end is not None:
        return res_begin, res_end
    else:
        raise AttributeError


def save_data(processed_data, name):
    df = pd.DataFrame(processed_data)
    df.set_index("seatNum")
    df.to_csv(name + ".csv")


def process_data(raw_data):
    if login_status:
        _raw_all = []
        _time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        _begin: str = ""
        _end: str = ""

        for _sub_list in raw_data:
            for seat in _sub_list:
                # print('inspecting id: ' + seat['seatNum'])

                state = seat.get("state", -1)

                if state == 2:
                    # partially occupied
                    _begin, _end = get_reserve_time(seat["seatId"])
                elif state == 3:
                    # fully occupied
                    _begin = TIME_BEGIN
                    _end = TIME_END
                elif state == 1:
                    # not occupied
                    _begin, _end = "", ""

                seat["begin"] = _begin
                seat["end"] = _end
                seat["catch time"] = _time

                _raw_all.append(seat)

        save_data(_raw_all, "asd")
    else:
        return


# 按间距中的绿色按钮以运行脚本。
if __name__ == "__main__":
    init()
    process_data([get_seats_data(154), get_seats_data(113)])
