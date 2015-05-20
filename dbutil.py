import time
from pymongo import MongoClient

conn = MongoClient()
db = conn.github

def run_aggregate(pipeline, verbose=True):
    start_time = time.time()
    db.watchers.aggregate(pipeline, allowDiskUse=True)
    if verbose: print "Runtime:", (time.time() - start_time)

def create_repo_to_users():
    pipeline = [
        { "$project": {
            "_id": 0,
            "login": 1,
            "ownerAndRepo": { "$concat": ["$owner","/","$repo"] }
        }},
        { "$group": { 
            "_id": "$ownerAndRepo",
            "users": { "$addToSet" :"$login" },
            "count": { "$sum" : 1},
        }},
        { "$out": "repoToUsers"},
    ]
    run_aggregate(pipeline)

def create_user_to_repos(num=0):
    pipeline = [
        { "$group": { 
            "_id": "$login",
            "repos": {"$addToSet": {"$concat": ["$owner","/","$repo"]}},
            "count": {"$sum": 1},
        }},
        { "$match": {
            "count" : { "$gt": num}
        }},
        { "$out": "userToRepos"},
    ]
    run_aggregate(pipeline)

def get_prefs(coll=db.repoToUsers, num_starred=10):
    query = coll.find({ "count": { "$gt": num_starred } })
    return {
        repo['_id']: repo['users']
        for repo in query
    }

# Pull MinHashes of repos from mongo into memory
def get_minhashes():
    return {
        repo['repo']: repo['hashes']
        for repo in db.minhash.find()
    }
