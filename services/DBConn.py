from pymongo import MongoClient
from pprint import pprint  # pretty print JSON

# Username = capstone, Password = "mongopassword", Database Name = hunter_collab
client = MongoClient(
    "mongodb://capstone:mongopassword@cluster0-shard-00-00-we2hu.mongodb.net:27017,"
    "cluster0-shard-00-01-we2hu.mongodb.net:27017,"
    "cluster0-shard-00-02-we2hu.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin"
    "&retryWrites=true")

adminDB = client.admin
db = client.hunter_collab


serverStatusResult = adminDB.command("serverStatus")
pprint(serverStatusResult)
