from flask import *
import mysql.connector
import json

app = Flask(__name__)

credentials = json.load(open("credentials.json", "r"))


@app.route('/timer', methods=['GET'])
def timer():
    database = mysql.connector.connect(
        host=credentials["host"],
        user=credentials["user"],
        passwd=credentials["password"],
        database=credentials["database"]
    )
    cursor = database.cursor()

    query = "SELECT * FROM solve_times;"

    cursor.execute(query)
    data = cursor.fetchall()

    cursor.close()
    database.close()
    return render_template("solve_stats.html", data=data)


@app.route('/', methods=['GET'])
def default():
    return redirect(url_for('timer'))
