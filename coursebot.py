import urllib.request,json,psycopg2,sys,time,telepot,threading
from configparser import ConfigParser
from telepot.loop import MessageLoop

signUp = "https://myub.buffalo.edu/"
help_msg = "Here are some valid commands:\n" + "/cid\n(shows your chat id)\n" + "/cse101\n(shows CSE101 course info)"
commands =['help','cid','alert']

# Function that takes in a course such as CSE341 splits and replace base URL to generate a URL to request data from.
# After getting data (json), decode and get necessary information to build a valid response to return to caller.
def courseInfo(course):
    n ='\n'
    dept = course[0:3]
    cnum = course[3:6]
    try:
        configData = config('url')
        api_url = configData['baseurl'].replace("[dept]",dept).replace("[cnum]",cnum)
        api_data = urllib.request.urlopen(api_url)
        resp = api_data.read().decode('utf-8')
        jsonF = json.loads(resp)
        seatsOpen = jsonF['courses'][0]['enrollment']['section'] - jsonF['courses'][0]['enrollment']['enrolled']
        pattern = jsonF['courses'][0]['when'][0]['pattern']
        time = jsonF['courses'][0]['when'][0]['dates']['start'] + '-' + jsonF['courses'][0]['when'][0]['dates']['end']
        room = jsonF['courses'][0]['room']
        instructor = jsonF['courses'][0]['instructor']
        return course + n + instructor + n + pattern + n + time + n + room + n + "Seats open: " + str(seatsOpen)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ("Course not found")
        elif e.code == 408:
            return ("Request timed out, please try again")
        elif e.code == 500:
            return ("Internal server error!!")
        else:
            return ("Sorry something went wrong, please try again")

# alertSystem adds courses that needs alert into a database to let checking keep track of how many courses need to be check
# alertSystem was also meant to do alertChecking but due to rapid coding and testing I forgot to replace them. Update soon but still works fine
def alertSystem(task,value):
    configData = config('db')
    retValue = {}
    try:
        con = psycopg2.connect(dbname=configData['database'], user=configData['user'], password=configData['password'])
        cur = con.cursor()
        if task == 'add':
            splitValue = value.split()
            cur.execute("INSERT INTO Course VALUES(%s,%s)",(splitValue[1],splitValue[0]))
            con.commit()
        else:
            retValue["hi"] = "bye"              # This part of alertSystem was meant to do alertCheck() will update soon.
    except psycopg2.Error as e:
        if con:
            con.rollback()
        if e.pgcode == "23505":
            retValue['duplicate'] = 'course'
        else:
            print("Error code: " + e.pgcode)
    finally:
        if con:
            con.close()
        return retValue

# alertCheck gets all the course from database that needs alert and call courseInfo.
# If seats are available, alert user that requested the alert.
def alertCheck():
    configData = config('db')
    queryTable = {}
    try:
        con = psycopg2.connect(dbname=configData['database'], user=configData['user'], password=configData['password'])
        cur = con.cursor()
        cur.execute("SELECT * FROM Course")
        for course in cur:
            print(course)
            queryTable[course[0]] = course[1]
    except psycopg2.Error as e:
        if con:
            con.rollback()
        print("Error code: " + e.pgcode)
    finally:
        if con:
            con.close()
    if queryTable:
        print(queryTable)
        for key in queryTable:
            msg = courseInfo(key)
            print(key)
            seatsAvailable = int(msg.split('Seats open: ',1)[1])
            if seatsAvailable > 0:
                alertMessage = str(seatsAvailable) + " seats available for " + key + "\n" + signUp
                bot.sendMessage(queryTable[key], alertMessage)
            time.sleep(30)

# Function that handles all incoming message from Telgram and determine if message is a valid request from a valid user and act accordingly.
def requestHandler(request):
    message = request['text']
    chat_id = request['chat']['id']

    print(chat_id, message)

    if message[0] != '/':
        return
    else:
        command = message.replace('/', '').split()
        if command[0] in commands or len(command[0]) == 6:
            if command[0] == 'cid':
                bot.sendMessage(chat_id, chat_id)
            elif command[0] == 'help':
                bot.sendMessage(chat_id, help_msg)
            elif command[0] == 'alert':
                if len(command) != 2 or len(command[1])!= 6:
                    bot.sendMessage(chat_id, "Invalid command!")
                else:
                    course = command[1].upper()
                    print(course)
                    msg = courseInfo(course)
                    if course not in msg:
                        if msg == "Internal server error!! Shutting down..":
                            bot.sendMessage(chat_id, msg)
                            sys.exit(1)
                        else:
                            bot.sendMessage(chat_id, "Course not found or something went wrong")
                    elif msg.split('Seats open: ',1)[1] != '0':
                        bot.sendMessage(chat_id, msg)
                        bot.sendMessage(chat_id, "Seats Available, not added into alert")
                    else:
                        bot.sendMessage(chat_id, msg)
                        value = str(chat_id) + ' ' + course
                        retValue = alertSystem('add', value)
                        if not retValue:
                            bot.sendMessage(chat_id, "Added into alert")
                        elif 'duplicate' in retValue:
                            bot.sendMessage(chat_id, "Course already in alert")
                        else:
                            bot.sendMessage(chat_id, "Not added into alert, try again")
            else:
                validUser = checkID(chat_id)
                if validUser == True:
                    course = command[0].upper()
                    print(course)
                    msg = courseInfo(course)
                    if msg == "Internal server error!! Shutting down..":
                        bot.sendMessage(chat_id,msg)
                        sys.exit(1)
                    else:
                        bot.sendMessage(chat_id, msg)
                else:
                    bot.sendMessage(chat_id, "Sorry, you are not authorized/system error")
        else:
            bot.sendMessage(chat_id, "Invalid command!")

# Check if reuqest is from a valid user by checking the valid user database
def checkID(chat_id):
    configData = config('db')
    validation = False
    try:
        con = psycopg2.connect(dbname=configData['database'], user=configData['user'], password=configData['password'])
        cur = con.cursor()
        cur.execute("SELECT EXISTS(SELECT * FROM Telegram WHERE id=%s)",(chat_id,))
        validation =cur.fetchone()[0]
    except psycopg2.Error as e:
        if con:
            con.rollback()
        print("Error code: " + e.pgcode)
    finally:
        if con:
            con.close()
        return validation

# Configuration function that gets necessary information from config.ini
def config(section):
    parser = ConfigParser()
    parser.read('config.ini')
    try:
        data ={}
        for item in parser.items(section):
            data[item[0]] = item[1]
    except ConfigParser.Error:
        print("Configuration error! Aborting...")
        sys.exit(1)
    finally:
        return data

# initialSetup function does all the initialSetup such as creating necessary database table if not exist. It also sets up Telegram token for request.
def initialSetup():
    configData = config('initial')
    try:
        con = psycopg2.connect(dbname=configData['database'], user=configData['user'], password=configData['password'])
        print("Connect successfully")
        cur = con.cursor()
        cur.execute("CREATE TABLE Course(Course TEXT PRIMARY KEY, Id INT)")
        print('Table "Course" created')
        con.commit()
    except psycopg2.Error as e:
        if con:
            con.rollback()
        if e.pgcode == "42P07":
            print("Duplicate table Course, nothing created")
        else:
            print("Error code: " + e.pgcode + " aborting...")
            sys.exit(1)
    try:
        cur.execute("CREATE TABLE Telegram(Id INT PRIMARY KEY, Name TEXT, type TEXT)")
        print('Table "Telegram" created')
        con.commit()
    except psycopg2.Error as e:
        if con:
            con.rollback()
        if e.pgcode == "42P07":
            print("Duplicate table Telegram, nothing created")
        else:
            print("Error code: " + e.pgcode + " aborting...")
            sys.exit(1)
    finally:
        if con:
            con.close()
    try:
        global bot
        bot = telepot.Bot(configData['token'])
        MessageLoop(bot, requestHandler).run_as_thread()
    except:
        print("Telegram bot connection error! Aborting...")
        sys.exit(1)

if __name__ == '__main__':
    initialSetup()
    alertCheck()
    t = threading.Timer(1800,alertCheck)
    t.start()
    while True:
        time.sleep(1)