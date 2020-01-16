#!/usr/bin/python3
### BEGIN INIT INFO
# Provides:          temperature-checker
# Required-Start:    $all
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: Regularly check temperature, email issues
### END INIT INFO

import daemon
import datetime
import os
import requests
import smtplib
import sys
import syslog
import time


class TemperatureChecker():
    IP_ADDRESS = '192.168.100.165'
    URL = 'http://%s:5000/temperature/' % (IP_ADDRESS)
    MIN_TEMPERATURE = 18.0
    TIMEOUT = 5
    SECONDS_BETWEEN_FAILED_TEMPERATURE_CHECKS = 2
    SECONDS_BETWEEN_TEMPERATURE_CHECKS = 60 * 60
    TEMPERATURE_LIST_SIZE_MAX = 7 * 24
    SEND_SUMMARY_EMAIL = 24
    ERROR_TEMPERATURE = -99.0
    TO_EMAIL = 'xxx@gmail.com'
    FROM_EMAIL = 'yyy@gmail.com'
    FROM_EMAIL_PASSWORD = 'zzz'

    def run(self):
        syslog.openlog(sys.argv[0])
        syslog.syslog(syslog.LOG_NOTICE, 'Process started')
        send_summary_counter = 0
        temperatures = []
        dates = []
        while True:
            # Retry getting temperature up to 3 times
            result = False
            temperature = TemperatureChecker.ERROR_TEMPERATURE
            attempts = 0
            while (attempts < 3) and (not (result == True)):
                attempts += 1
                [result, temperature] = self.get_temperature()
                if not result:
                    time.sleep(TemperatureChecker.SECONDS_BETWEEN_FAILED_TEMPERATURE_CHECKS)

            current_time = datetime.datetime.now().strftime('%y/%m/%d %H:%M:%S')
            # Process temperature results
            if temperature == TemperatureChecker.ERROR_TEMPERATURE:
                message = 'Temperature Checker\n\nError getting garage temperature at %s, %s' % (current_time, result)
                self.send_email('Temperature Checker - Error', message)
                syslog.syslog(syslog.LOG_NOTICE, message)
            elif temperature < TemperatureChecker.MIN_TEMPERATURE:
                message = 'Temperature Checker\n\nHeat the room in the garage, %sC at %s' % (temperature, current_time)
                self.send_email('Temperature Checker - Garage is cold', message)
                syslog.syslog(syslog.LOG_NOTICE, message)
            else:
                syslog.syslog(syslog.LOG_NOTICE, 'Garage temperature at %s is fine, %sC' % (current_time, temperature))

            # Track temperature trend
            temperatures.append(temperature)
            dates.append(current_time)
            if len(temperatures) > TemperatureChecker.TEMPERATURE_LIST_SIZE_MAX:
                temperatures.pop(0)
                dates.pop(0)

            # Send summary
            send_summary_counter += 1
            if send_summary_counter == TemperatureChecker.SEND_SUMMARY_EMAIL:
                send_summary_counter = 0
                message = 'Temperature Checker\n\nTemperature history: %s\nDate history: %s' % (temperatures, dates)
                self.send_email('Temperature Checker - Summary', message)
                syslog.syslog(syslog.LOG_NOTICE, 'Garage temperature summary sent: %s' % (temperatures))

            time.sleep(TemperatureChecker.SECONDS_BETWEEN_TEMPERATURE_CHECKS)


    def send_email(self, subject, text):
        # creates SMTP session 
        s = smtplib.SMTP('smtp.gmail.com', 587) 
          
        # start TLS for security 
        s.starttls() 
          
        # Authentication 
        s.login(TemperatureChecker.FROM_EMAIL, TemperatureChecker.FROM_EMAIL_PASSWORD)
          
        # sending the mail 
        message = 'Subject: {}\n\n{}'.format(subject, text)
        s.sendmail(TemperatureChecker.FROM_EMAIL, TemperatureChecker.TO_EMAIL, message) 
        
        # terminating the session 
        s.quit()


    def get_temperature(self):
        try:
            response = requests.get(TemperatureChecker.URL, timeout=TemperatureChecker.TIMEOUT)
            if response.ok:
                result = 'Temperature is %s' % (response.text)
                return [response.ok, float(response.text)]
            else:
                result = [response, TemperatureChecker.ERROR_TEMPERATURE]
        except Exception as ex:
            result = ex
        return [result, TemperatureChecker.ERROR_TEMPERATURE]


if __name__ == "__main__":
    #context = daemon.DaemonContext()
    #context.open()
    #with context:
        n = os.fork()
        if n > 0:
            # Parent process
            pass
        else:
            # Child process
            temperature_checker = TemperatureChecker()
            temperature_checker.run()
