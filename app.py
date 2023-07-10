import os
import threading
import time

from twilio.base.exceptions import TwilioRestException

import main
from flask import Flask, render_template, redirect, make_response, request
from threading import Thread
import logging
from main import client

## Variables

app = Flask(__name__)
t1 = None  # Declare the thread variables outside the functions
t2 = None
stop_event = threading.Event()  # Create an event to signal the thread to stop

# Create a logger
logger = logging.getLogger(__name__)
# Set the logging level
logger.setLevel(logging.DEBUG)
# Create a file handler
file_handler = logging.FileHandler('logs.txt')
# Create a formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)
stop_logging_event = threading.Event()


@app.route('/start', methods=['POST'])
def start():
    on_call_number = request.form['oncall']
    start_main(on_call_number)
    logger.info(f"Starting PriorityOne with on-call number: {on_call_number}")
    try:
        message = client.messages.create(
            body="You are on-call. Please make sure to have your phone with you at all times until you log off",
            from_='Number',
            to=on_call_number
        )
    except TwilioRestException as e:
        logger.info('Error sending SMS:' + str(e))
    logger.info(f'SMS sent to on-call number: {on_call_number}')
    return redirect('/')


def start_main(on_call_number):
    global t2, stop_event
    if t2 and t2.is_alive():
        stop_event.set()
        t2.join()
    stop_event.clear()
    t2 = threading.Thread(target=main.main, daemon=True, args=(on_call_number, stop_event,))
    t2.start()


@app.route('/stop', methods=['POST'])
def stop_script():
    global stop_event
    if t2 and t2.is_alive():
        stop_event.set()  # Set the event to signal the thread to stop
        t2.join()
        logger.info("PriorityOne main.py stopped!")
    else:
        logger.debug("PriorityOne main.py is not running")
    return redirect('/')


@app.route('/exportlogs')
def export_logs():
    with open('logs.txt', 'r') as f:
        logs = f.readlines()
    response = make_response('\n'.join(logs))
    response.headers["Content-Disposition"] = "attachment; filename=logs.txt"
    logger.info("Logs exported")
    return response


def start_app():
    global app
    app.run(host="0.0.0.0", port=8000)


@app.route("/")
def hello():
    with open("logs.txt", "r") as f:
        log_output = f.read()
    return render_template("logs.html", logs=log_output)


@app.route("/clearlogs", methods=["POST"])
def clear_logs():
    try:
        with open("logs.txt", "w") as f:
            f.write("")  # write empty string to clear file contents
    except FileNotFoundError:
        logger.error("File not found")
    return redirect("/")


if __name__ == "__main__":
    t1 = Thread(target=start_app)
    t1.start()
    t1.join()
