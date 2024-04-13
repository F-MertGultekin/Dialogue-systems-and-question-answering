
from datetime import datetime,timedelta
import requests
import json
import urllib
import random
from geopy.distance import geodesic




#Base URL to fetch Google Maps data 
baseUrl= "https://maps.googleapis.com/maps/api/geocode/json?"
GoogleMapsAPI = ""
OpenWeatherMapAPI = ""
format = '%Y-%m-%d %H:%M:%S'
VasttrafikAPI = ""

#Weather forecast frame
class WeatherForecast:
    
    #Keywords to find the weather forecast context
    keyWords = ['weather','feels like','sunny','pressure','humidity','sky','rain','cloudy','wind','speed','windy','hot','cold','sunset','sunrise','temperature']
    invalidDateForm = False # TODO For the februay, ....
    HistoricalWeatherData = False # TODO We can say that we cannot provide historical weather forecast
    
    #Empty Constructor to initialize frame/form
    def __init__(self):
        self.frame = [['date',None],['time',None],['location',None],['closestDateTime',None] ]
        self.weather = 0.0
        #TODO, add this information if it is asked.
        self.pressure = 0.0
        self.humidity = 0.0
        self.main = " " #Clear, rainy, cloudy, sunny.....
        self.windSpeed= 0.0
        self.maxTemp = 0.0
        self.minTemp = 0.0
        self.userInput = None
        
    def dateTrimmer(self,dateArray):
        # if the month is starts with 0, like 01, 02....09
        if int(dateArray[1][0]) == 0:
            dateArray[1] = dateArray[1][1]
        # if the day is starts with 0, like 01, 02....09
        if int(dateArray[2][0]) == 0:
            dateArray[2] = dateArray[2][1]

        return dateArray[1], dateArray[2]    
            
    # Data format is like 2023/02/28 yyyy-mm-dd
    def fillDate(self, word):
        splitter = '-' #Date splitter will  be always -  
        dateArray= None
        if  len(word) in range(8, 11) and self.frame[0][1] == None: 
            if '/' in word: 
                dateArray = word.split('/')
            elif '-' in word: 
                dateArray = word.split('-')
            elif '.' in word: 
                dateArray = word.split('.')
        
            dateArray[1], dateArray[2]  = self.dateTrimmer(dateArray)
        
            if int(dateArray[0]) in range(2000,2025) and int(dateArray[1]) in range(1,13) and int(dateArray[2]) in range(1,32):
                self.frame[0][1] = dateArray[0] + splitter + dateArray[1] + splitter + dateArray[2] #YYYY-MM-DD
        #TODO ==> check for the exceptions such as days can not be 30 in February 
        #TODO ==> if date format is wrong, return false flag
    def fillTime(self, word, timeFormat):
        if not timeFormat and len(word) == 5 and self.frame[1][1] == None:
            timeArray = word.split('.' if '.' in word else ':')
            if int(timeArray[0]) in range(0,24) and int(timeArray[1]) in range(0,60):
                self.frame[1][1] = timeArray[0] + ':' + timeArray[1] + ":00"
        if timeFormat: #if format it like 1a.m
            hour = word[0]
            minute = '00'
            if 'a.m' in word and int(hour) in range (1,13):
                
                self.frame[1][1] = hour + ':' + minute +":00"
            elif 'p.m' in word and hour in range (1,13):
                hour = int(word[0]) + 12
                self.frame[1][1] = str(hour) + ':' + minute+ ":00"
                #TODO ==> if time format is wrong, return false flag
                #TODO ==> if time is like 15a.m, add control for it

    def fillLocation(self,word):
        coordinatesData = self.sendRequestToGoogle(word)
        if coordinatesData.get("results"): 
            self.frame[2][1] = coordinatesData.get("results")[0].get("formatted_address")
            forecastData = self.sendRequestToWeatherForecastProvider(coordinatesData)

            dt_txt_list = [entry['dt_txt'] for entry in forecastData['list']]
            # parse the dt_txt values into datetime objects
            date_times_list = [datetime.strptime(dt_txt, format) for dt_txt in dt_txt_list]
            closestDateTime,index = self.findClosestTime(date_times_list)
            temperature = forecastData['list'][index]['main']['temp']
            #TODO check if we need this line ==> self.frame[3][1]= closestDateTime
            self.weather = temperature
            self.pressure = forecastData['list'][index]['main']['pressure']
            self.humidity = forecastData['list'][index]['main']['humidity']
            self.maxTemp = forecastData['list'][index]['main']['temp_max']
            self.minTemp = forecastData['list'][index]['main']['temp_min']
            self.windSpeed= forecastData['list'][index]['wind']['speed']
            self.main = forecastData['list'][index]['weather'][0]['description']
    def findTemperature(self,forecastData, closest_date_time):
        for entry in forecastData['list']:
            # Check if the "dt_txt" value matches the specific value
            if datetime.strptime(entry['dt_txt'], format) == closest_date_time:
                # Access the "temp" value using the "main" key
                temp = entry['main']['temp']
                return temp

    def sendRequestToGoogle(self, word):
        parameters = {"address": word, "key": GoogleMapsAPI}
        req = requests.get(f"{baseUrl}{urllib.parse.urlencode(parameters)}")
        data = json.loads(req.content)
        return data

    def sendRequestToWeatherForecastProvider(self, coordinatesData):
        lat = coordinatesData.get("results")[0].get("geometry").get("location").get("lat")
        lon = coordinatesData.get("results")[0].get("geometry").get("location").get("lng")
        response = requests.get("https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s&units=metric" % (lat, lon, OpenWeatherMapAPI))
        forecast = json.loads(response.text)
        #In response there will be lots of weather information on different time.
        #First weather information is the current one and then for every 3 hours, there is one info under list 
        #total 5 days forecast is available  
        return forecast
    def findClosestTime(self,date_times_list):
        # Convert the provided dates and times into datetime objects
        date_time = None
        # Provide a new date and time to compare
        #If the algorithm first finds the location word then it is going to send weather url but we need to check if the date and time is empty or not// there might be an error
        if self.frame[0][1] == None or self.frame[1][1] == None:
            self.checkFrame()
        else:
            date_time = self.frame[0][1] + " " + self.frame[1][1]
        formatted_new_date_time = datetime.strptime(date_time, format)

        # Calculate the differences between the new date and time and each date and time in the list
        differences = [abs(dt - formatted_new_date_time) for dt in date_times_list]

        # Find the minimum difference and corresponding date and time
        min_difference = min(differences)
        closest_date_time = date_times_list[differences.index(min_difference)]
        return closest_date_time, differences.index(min_difference)
    
    def fillFrame(self, userInput):
        
        words = userInput.split()
        timeFormat = False
        
        for word in words:
            #Date must be in the form of YYYY-MM-DD
            #TODO except other types of dates like May 10 2023 ...
            if '/' in word or '-' in word or '.' in word:
                self.fillDate(word)
                if not self.frame[0][1] == None:
                    continue

            #check  if the input has time information and fill
            if ':' in word or '.' in word:
                self.fillTime(word,timeFormat)
                continue
            elif "a.m" in word or "p.m" in word:
                self.fillTime(word,not timeFormat)
                continue
            #Check if the input has location information and fill
            if self.frame[2][1] == None:
                self.fillLocation(word)
                continue
        self.checkFeatures(userInput)

    def checkFeatures(self, userInput):
            #This part is not generic
        if "pressure" in userInput.lower():
            print("Computer: Pressure level on that time will be "+ str(self.pressure))
        if "humidity" in userInput.lower():
            print("Computer: Humidity level on that time will be "+ str(self.humidity))
        if "what is the weather like" in userInput.lower():
                print("Computer: Weather on that time will be "+ self.main)
        if "wind speed" in userInput.lower() or "speed of the wind" in userInput.lower():
                print("Computer: Wind speed on that time will be "+ str(self.windSpeed) + "km/h")
        if "minimum temperature" in userInput.lower():
            print("Computer: Minimum temperature on that time will be "+ str(self.minTemp) + "celcius degree")
        if "maximum temperature" in userInput.lower():
            print("Computer: Maximum temperature on that time will be "+ str(self.maxTemp) + "celcius degree")
    
    def checkDate(self,userInput):
        words = userInput.split()
        for word in words:
            if '/' in word or '-' in word or '.' in word:
                self.fillDate(word)
                break

    def checkTime(self,userInput):
        #Check if the base sentence involves a time
        timeFormat = False
        words = userInput.split()
        for word in words:
            if ':' in word:
                self.fillTime(word,timeFormat)
                break
            if "a.m" in word or "p.m" in word:
                self.fillTime(word,not timeFormat)
                break

    def includesDigit(self, word):
        contains_int = False
        for char in word:
            if char.isdigit():
                contains_int = True
                return contains_int
        return contains_int
    
    def IsTimeOkay(self,date_and_time):
        now = datetime.now()

        # Convert the given date and time into a datetime object
        given_date_time = datetime.strptime(date_and_time, format)
        difference = given_date_time - now

        # Check if the given date and time is in the past
        if given_date_time < now:
            print('Computer: The given date and time is in the past. Please specify the date and time again in this format YYYY-MM-DD HH:MM')
            return False
        elif difference > timedelta(days=5):
            print('Computer: The given date and time is more than 5 days later than now. Please specify the date and time again in this format YYYY-MM-DD HH:MM')        
            return False
        else: 
            return True
        
    def checkFrame(self):
        #Check if date is filled, else ask relevant questions
        
        while self.frame[0][1] == None: 
            print("Computer: I have lack of information, could you specify the date?")  
            userInput = input("You: ").lower()
            self.checkDate(userInput)
        while self.frame[1][1] == None: 
            print("Computer: I have lack of information, could you specify the time?")  
            userInput = input("You: ").lower()
            self.checkTime(userInput)
        while self.frame[2][1] == None:
                print("Computer: I have lack of information, could you specify the city or street?")  
                userInput = input("You: ").lower()
                words = userInput.split()
                for word in words: 
                    if not self.includesDigit(word): # if the string does not contaion integer (time and date)
                        self.fillLocation(word)

        if not self.frame[0][1] == None and not self.frame[1][1] == None and not self.IsTimeOkay(self.frame[0][1]+" "+ self.frame[1][1]):
            userInput = input("You: ").lower()
            self.frame[0][1]=None
            self.frame[1][1]=None
            self.fillFrame(userInput)
            self.checkFrame()
              
        print("Computer: " + self.frame[2][1] + " on " + self.frame[0][1] + " at " + self.frame[1][1] + " will be " + str(self.weather) + " celcius degree")

class Restaurant:
    keyWords = ['restaurant','eat','lunch','dinner',"breakfast",'meal','coffee', "hamburger","pizza","pasta","kebab"]
    restaurantdata = [["kebab pizza","gibraltargatan",'cheap'], ["subway","lindholmspiren",'normal'], ["mcDonalds","nordstan",'expensive'], ["La Cucina Italiana","skaanegatan","premium"]]
    streets = {
        "andralanggatan":(57.69896, 11.946480309255652),
        "forstalanggatan":(57.699744, 11.946120338787129),
        "hagahygata":(57.69847869597871, 11.956910535202512),
        "jarntorgsgatan":(57.70110386149006, 11.954101914011082),
        "linnegatan":(57.69528672268305, 11.951725382075884),
        "masthuggsterrassen":(57.69788095600096, 11.942953258263865),
        "vasagatan":(57.69855878966971, 11.968145836812283),
        "ostrahamngatan":(57.709028, 11.966999)
    }
    street_names = ["andralanggatan","forstalanggatan","haganygata","jarntorgsgatan", "linnegatan","masthuggsterrassen","vasagatan","ostrahamngatan"]
    # Dictionary containing the addresses and their coordinates
    restaurantsAddresses = {
        'gibraltargatan': (57.696251, 11.969616),
        'lindholmspiren': (57.707701, 11.938809),
        'nordstan': (57.707635, 11.972750),
        'skaanegatan': (57.698738, 11.973874)
    }
    myAddress = {"plejadgatan": (57.704883, 11.933065)}

    def __init__(self):
        self.frame = [['queryAddress',None],['location',None],['price', None],['restaurant', None],['distance',None],['restaurant_street',None]]

    def distance(self, userAddress):
    # Calculate the distances between each street and the four addresses
        min = 100000.0
        for restaurant in self.restaurantsAddresses:
        
            distance = geodesic(self.streets[userAddress], self.restaurantsAddresses[restaurant]).km
            if distance < min:
                min = distance
                min_distance_restaurant = restaurant
        
        return min_distance_restaurant, min
    
    def distanceToMyHome(self):
    # Calculate the distances between each street and the my address
        min = 100000.0
        for restaurant in self.restaurantsAddresses:
        
            distance = geodesic(self.myAddress["plejadgatan"], self.restaurantsAddresses[restaurant]).km
            if distance < min:
                min = distance
                min_distance_restaurant = restaurant

        return min_distance_restaurant, min
    def findRestaurantName(self, street):
        for i,restaurant in enumerate(self.restaurantdata):
            if restaurant[1] == street:
                return restaurant[0],restaurant[2]

    def fillFrame(self,userInput):
        words = userInput.split()
        for i, word in enumerate(words):
            if "my" in word and i < len(words)-1 and "address" in words[i+1]:
                self.frame[0][1] = "plejadgatan"
                restaurant_street, distance = self.distanceToMyHome()
                restaurant_name , restaurant_price = self.findRestaurantName(restaurant_street)
                self.frame[2][1] = restaurant_price
                self.frame[3][1] = restaurant_name
                self.frame[4][1] = distance
                self.frame[5][1] = restaurant_street

            elif word in self.street_names:
                
                restaurant_street, distance = self.distance(word)
                self.frame[0][1] = word
                restaurant_name , restaurant_price = self.findRestaurantName(restaurant_street)
                self.frame[2][1] = restaurant_price
                self.frame[3][1] = restaurant_name
                self.frame[4][1] = distance
                self.frame[5][1] = restaurant_street
    def checkFrame(self):
        if self.frame[0][1] == None:
            print("Please enter an address either your address or any address to query")
        if self.frame[0][1] == "plejadgatan" and not self.frame[3][1] == None:
            print("The closest restaurant to your address is "+ str(self.frame[3][1]))
        if not self.frame[0][1] == None and not self.frame[0][1] == "plejadgatan" and not self.frame[3][1] == None:
            print("The closest restaurant to address"+ str(self.frame[0][1]) +" is "+ str(self.frame[3][1]))
        if not self.frame[4][1] ==None:
            print("The distance of the restaurant is "+ str(self.frame[4][1]))
        if not self.frame[2][1] ==None:
            print("Generally prices of the restaurant is relatively "+ str(self.frame[2][1]))
        if not self.frame[5][1] ==None:
            print("The restaurant address is " + str(self.frame[2][1]))
# Define the bus/tram stops and lines
stops = {
    "centralstationen": ["1","4" "16", "19"],
    "kungsportsplatsen": ["2", "13", "16", "19"],
    "brunnsparken": ["1", "2", "3", "19"],
    "marklandsgatan": ["2", "4", "5", "13"],
    "chapmanstorg": ["10", "13", "16", "19"],
    "saltholmen": ["5","11"]
}
timetable = {
        "1_centralstationen": [f"{hour:02d}:00" for hour in range(5, 25)],
        "1_brunnsparken": [f"{hour:02d}:03" for hour in range(5, 25)],
        "2_kungsportsplatsen": [f"{hour:02d}:06" for hour in range(5, 25)],
        "2_brunnsparken": [f"{hour:02d}:09" for hour in range(5, 25)],
        "2_marklandsgatan": [f"{hour:02d}:12" for hour in range(5, 25)],#########
        "3_brunnsparken": [f"{hour:02d}:15" for hour in range(5, 25)],
        "4_centralstationen": [f"{hour:02d}:18" for hour in range(5, 25)],
        "4_marklandsgatan": [f"{hour:02d}:21" for hour in range(5, 25)],##########
        "5_marklandsgatan": [f"{hour:02d}:23" for hour in range(5, 25)],###########
        "5_saltholmen": [f"{hour:02d}:26" for hour in range(5, 25)],###########
        "10_chapmanstorg": [f"{hour:02d}:27" for hour in range(5, 25)],###########
        "11_saltholmen": [f"{hour:02d}:28" for hour in range(5, 25)],###########
        "13_kungsportsplatsen": [f"{hour:02d}:30" for hour in range(5, 25)],
        "13_marklandsgatan": [f"{hour:02d}:33" for hour in range(5, 25)],###########
        "13_chapmanstorg": [f"{hour:02d}:36" for hour in range(5, 25)],###########
        "16_centralstationen": [f"{hour:02d}:39" for hour in range(5, 25)],
        "16_kungsportsplatsen": [f"{hour:02d}:42" for hour in range(5, 25)],
        "16_chapmanstorg": [f"{hour:02d}:45" for hour in range(5, 25)],###########
        "19_centralstationen": [f"{hour:02d}:48" for hour in range(5, 25)],
        "19_kungsportsplatsen": [f"{hour:02d}:51" for hour in range(5, 25)],
        "19_brunnsparken": [f"{hour:02d}:54" for hour in range(5, 25)],
        "19_chapmanstorg": [f"{hour:02d}:57" for hour in range(5, 25)]###########
}

class Bus:

    keyWords = ['bus','tram','train','stop','transport', 'go' , 'travel', 'hop in' , 'hop off', 'line', "time", "minutes"]
    
    def __init__(self,):
        self.frame = [['from', None], ['to', None], ['minute', None], ['arrivalTime', None],['lineKeyword', False],['line', None],['timeKeyword', False]]        
    # Define a function to fetch the next bus/tram arrival time
    def fillFrame(self, userInput):
        
        words = userInput.split()
        for i, word in enumerate(words):
            if word.lower() == "from" and i < len(words)-1 and words[i+2] == "to":
                self.frame[0][1]  = words[i+1]
                continue
            #check  if the input has time information and fill
            elif word.lower() == "to" and i < len(words)-1 and words[i-2] == "from":
                self.frame[1][1] = words[i+1]
                continue
            elif word.lower() == "line":
                self.frame[4][1] = True
            elif word.lower() == "minute" or word.lower() == "time" or word.lower() == "when" or word.lower() == "transport" or word.lower() == "travel":
                self.frame[6][1] = True

           
       
    def checkFrame(self):    
        # Check if the given stops are valid
        somethingWrong = False
        if somethingWrong == False: 
            if self.frame[0][1] not in stops:
                print("Computer: Sorry, define a valid departure bus/tram stop .")
                somethingWrong = True
            if self.frame[1][1] not in stops:
                print("Computer: Sorry, define is not a valid destination bus/tram stop.")
                somethingWrong = True
        
        
        if somethingWrong == False: 
            # Get the bus/tram lines that connect the two stops
            common_lines = list(set(stops[self.frame[0][1]]) & set(stops[self.frame[1][1]]))
            
            # Check if there are any lines that connect the two stops
            if not common_lines:
                print("Computer: Sorry, there are no bus/tram lines that connect "+ self.frame[0][1] + " and " + self.frame[1][1] + ".")
                somethingWrong = True

        if somethingWrong == False:    
            # Fetch the next arrival time for each line
            now = datetime.now().strftime("%H:%M")# Get the current time
            arrivals = []
            min_time_diff = float('inf')
            now = int(now[:2]) * 60 + int(now[3:])
            closest_time = ""
            
            for line in common_lines:
                for lines_stops in timetable:
                    array_lines_stop = lines_stops.split('_')
                    if array_lines_stop[0] == line and array_lines_stop[1] in self.frame[0][1]:
                        for times in timetable[lines_stops]:
                            next_arrival = int(times[:2]) * 60 + int(times[3:])
                            
                            
                            time_diff = next_arrival - now

                            if time_diff > 0 and time_diff < min_time_diff:
                                closest_time = times
                                min_time_diff = time_diff
                                self.frame[5][1] = array_lines_stop[0]
                        
            arrivals.append(datetime.strptime(closest_time, "%H:%M").time())
            self.frame[2][1] = min_time_diff
        # Check if any arrival times were found
            if not arrivals:
                print("Computer: Sorry, no bus/tram arrivals were found from "+ self.frame[0][1] + " to " + self.frame[1][1] + ".")
                somethingWrong = True


        if somethingWrong == False:
            if self.frame[4][1]:
                print("Computer: You need to get the bus/tram number "+ self.frame[5][1])
            elif self.frame[6][1]:
                self.frame[3][1] = min(arrivals) # Find the next arrival time
                
                if self.frame[2][1] == 0:
                    print("Computer: The next bus/tram from " + str(self.frame[0][1]) + " to " + str(self.frame[1][1]) + " is arriving now. Hurry Up!")
                else:
                    print("Computer: The next bus/tram from " + str(self.frame[0][1]) + " to " + str(self.frame[1][1]) + " will be in " + str(self.frame[0][1]) + " in " +str(min_time_diff) + " minutes (at " + str(self.frame[3][1]) + " ).")
                    now = datetime.now().strftime("%H:%M")# Get the current time
                    print("Computer: INFO: The time is now "+ now)




#Method to extract context from intitial question
def getContext(userInput):
    context = None
    words = userInput.split()
    for word in words:
        if word in WeatherForecast.keyWords:
            context = WeatherForecast()
            context.userInput = userInput
        if word in Restaurant.keyWords:
            context = Restaurant()
        if word in Bus.keyWords: 
            context = Bus()
    return context

def closeDialogueCheck(userInput):
    closeKeywords = ['bye','take care!' ,'see you', 'no thanks','goodbye']
    for keywords in closeKeywords:
        if keywords in userInput:
            return True

def initialize():
    closeFlag = False
    while not closeFlag:
        print("Computer: What can I help you with?")
        userInput = input("You: ").lower()
        context = getContext(userInput)
        if context == None:
            closeFlag = closeDialogueCheck(userInput)
            if not closeFlag:
                print("Computer: Could you please ask me something about i can understand?")
            continue
        context.fillFrame(userInput)
        context.checkFrame()
    print("Computer: Goodbye. Have a nice day!")

initialize()

