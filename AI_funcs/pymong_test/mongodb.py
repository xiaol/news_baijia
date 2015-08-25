import pymongo
from tweepy import API
# Connection to Mongo DB
try:
    conn=pymongo.MongoClient()
    print "Connected successfully!!!"
except pymongo.errors.ConnectionFailure, e:
   print "Could not connect to MongoDB: %s" % e

db = conn.mydb
collection = db.my_collection
print collection
doc = {"name":"Alberto","surname":"Negron","twitter":"@Altons"}
collection.insert(doc)

lookup = 'BigData'
api = API()

search = []
page = 1
maxPage = 10
while page <= maxPage:
    tweets = api.search(lookup, page=page)
    for tweet in tweets:
        search.append(tweet)
    page += 1