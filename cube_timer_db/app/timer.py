from flask import *
import mysql.connector
import json
import time
import random
from datetime import date
from tabulate import tabulate
import RPi.GPIO as GPIO

button = 18
green_led = 3
red_led = 2

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(green_led, GPIO.OUT)
GPIO.setup(red_led, GPIO.OUT)

app = Flask(__name__)


def show_session(session_dates, session_scrambles, session_times, session_penalties, session_averages):
    # Display data to screen
    console_data = []
    for q in range(0, 5):
        today_q = session_dates[q]
        scramble_q = session_scrambles[q]
        solve_time_q = session_times[q]
        penalty_q = session_penalties[q]
        average_q = session_averages[q]
        each_solve = [today_q,scramble_q,solve_time_q,penalty_q,average_q]
        console_data.append(each_solve)

    print(tabulate(console_data, headers=["Date", "Scramble", "Time", "Penalty", "Average"]))


def get_scramble():
    scramble = ""
    scramble_list = []
    move_count = 0

    face = ["R", "L", "F", "B", "U", "D"]
    turn = ["", "2", "'"]

    while move_count < 20:

        if move_count != 19:
            rand_face = face[random.randint(0, len(face) - 1)]
            rand_turn = turn[random.randint(0, len(turn) - 1)]

            move = rand_face + rand_turn + " "
        else:
            rand_face = face[random.randint(0, len(face) - 1)]
            rand_turn = turn[random.randint(0, len(turn) - 1)]

            move = rand_face + rand_turn

        if len(scramble_list) == 0:
            scramble_list.append(move)
            move_count += 1
        else:
            opposite_face = ""
            if rand_face == "R":
                opposite_face = "L"
            elif rand_face == "L":
                opposite_face = "R"
            elif rand_face == "F":
                opposite_face = "B"
            elif rand_face == "B":
                opposite_face = "F"
            elif rand_face == "U":
                opposite_face = "D"
            elif rand_face == "D":
                opposite_face = "U"

            while rand_face == scramble_list[-1][0]:
                if move_count != 19:
                    rand_face = face[random.randint(0, len(face) - 1)]
                    rand_turn = turn[random.randint(0, len(turn) - 1)]
                    move = rand_face + rand_turn + " "
                else:
                    rand_face = face[random.randint(0, len(face) - 1)]
                    rand_turn = turn[random.randint(0, len(turn) - 1)]
                    move = rand_face + rand_turn

            if len(scramble_list) > 1:
                while rand_face == scramble_list[-2][0] and opposite_face == scramble_list[-1][0]:
                    if move_count != 19:
                        rand_face = face[random.randint(0, len(face) - 1)]
                        rand_turn = turn[random.randint(0, len(turn) - 1)]
                        move = rand_face + rand_turn + " "
                    else:
                        rand_face = face[random.randint(0, len(face) - 1)]
                        rand_turn = turn[random.randint(0, len(turn) - 1)]
                        move = rand_face + rand_turn

            scramble_list.append(move)
            move_count += 1

    for l in range(0, 20):
        move = scramble_list[l]
        scramble += move

    return scramble


def store_solve_data():
    # Load database user credentials from JSON
    credentials = json.load(open("credentials.json", "r"))

    # Connect to database
    database = mysql.connector.connect(
        host=credentials["host"],
        user=credentials["user"],
        passwd=credentials["password"],
        database=credentials["database"]
    )

    # Create cursor object that executes database commands
    cursor = database.cursor()

    # get date
    date_today = date.today()
    today = date_today.strftime("%b-%d-%Y")
    session_dates.append(today)

    scramble = get_scramble()
    print(scramble)
    session_scrambles.append(scramble)

    print("Press the button to start 15s inspection")
    countdown = 15

    solve_ended = False
    timer_state = False
    while True:
        if solve_ended == True:
            break
        input_state = GPIO.input(button)
        if input_state == False and timer_state == False:
            GPIO.output(green_led, GPIO.HIGH)
            while countdown > 0:
                if countdown == 1:
                    print(str(countdown) + "\n", sep=' ', end='', flush=True)
                else:
                    print(str(countdown) + " ", sep=' ', end='', flush=True)
                time.sleep(1)
                countdown -= 1
            GPIO.output(red_led, GPIO.LOW)
            start_time = time.time()
            timer_state = True
            print("Timer started")
            time.sleep(0.5)
        elif input_state == False and timer_state == True:
            GPIO.output(green_led, GPIO.LOW)
            GPIO.output(red_led, GPIO.HIGH)
            end_time = time.time()
            print("Timer stopped")
            solve_time = round(end_time-start_time, 3)
            solve_ended = True
            timer_state = False
            time.sleep(0.5)

    print(solve_time)
    penalty = input("p / +2 / DNF: ")
    while penalty != "p" and penalty != "+2" and penalty != "DNF":
        penalty = input("\tp / +2 / DNF: ")

    if penalty == "p":
        pass
    elif penalty == "+2":
        solve_time = round(solve_time+2, 3)
    elif penalty == "DNF":
        solve_time = "DNF"

    print(str(solve_time) + '\n')
    session_times.append(solve_time)
    session_penalties.append(penalty)

    # calculate session average
    average = ""
    if len(session_times) == 5:
        slowest_solve = 0
        if session_times[0] != "DNF":
            fastest_solve = session_times[0]
        elif session_times[1] != "DNF":
            fastest_solve = session_times[1]

        total_times = 0
        dnf_count = 0
        for i in range(0, 5):
            if session_times[i] == "DNF":
                dnf_count += 1

        if dnf_count > 1:
            average = "DNF"

        elif dnf_count == 1:
            session_times.remove("DNF")
            fastest_solve = session_times[0]
            for j in range(0, 4):
                if session_times[j] < fastest_solve:
                    fastest_solve = session_times[j]
                total_times += session_times[j]

            total_times -= fastest_solve
            average = round(total_times/3, 3)

        elif dnf_count == 0:
            for k in range(0, 5):
                if session_times[k] > slowest_solve:
                    slowest_solve = session_times[k]
                if session_times[k] < fastest_solve:
                    fastest_solve = session_times[k]

                total_times += session_times[k]

            total_times -= slowest_solve
            total_times -= fastest_solve
            average = round(total_times/3, 3)

        session_averages.append("")
        session_averages.append("")
        session_averages.append("")
        session_averages.append("")
        session_averages.append(average)

    if average == "":
        data = (today,scramble,solve_time,penalty,average)
    else:
        data = (today,scramble,solve_time,penalty,average)

    # SQL insert statement
    insert_sql = "INSERT INTO `solve_times` (`the_date`, `algorithm`, `solve_time`, `solve_status`, `session_average`) VALUES (%s,%s,%s,%s,%s);"

    cursor.execute(insert_sql,data)

    # Commit insert to database
    database.commit()

    # Close database connection
    cursor.close()
    database.close()

    time.sleep(0.5)


# DRIVER
session_dates = []
session_scrambles = []
session_times = []
session_penalties = []
session_averages = []

GPIO.output(red_led, GPIO.HIGH)

for i in range(0, 5):
    store_solve_data()

if len(session_times) == 5:
    # Display table
    show_session(session_dates,session_scrambles,session_times,session_penalties, session_averages)
