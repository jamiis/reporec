#!/usr/bin/env python

import json, time
from collections import defaultdict
from functools import partial

import dbutil, minhash

def parse_json(path,key,verbose=True):
    start_time = time.time()
    result = {}
    with open(path) as f:
        for d in json.load(f):
            result[d["_id"]] = set(d[key])
    if verbose:
        elapsed = time.time() - start_time
        print "Parsed:", len(result), key
        print "Runtime:", elapsed, "seconds"
    return result

def parse_repo_to_users_json():
    return parse_json("repoToUsers.json", "users")

def parse_user_to_repos_json():
    return parse_json("userToRepos.json", "repos")

def sim_distance(prefs,person1,person2):
    # Get the list of shared_items
    si={}
    for item in prefs[person1]:
        if item in prefs[person2]:
            si[item]=1
    # if they have no ratings in common, return 0
    if len(si)==0: return 0
    # Add up the squares of all the differences
    sum_of_squares=sum([pow(prefs[person1][item]-prefs[person2][item],2)
        for item in prefs[person1] if item in prefs[person2]])
    return 1/(1+sum_of_squares)

# Returns the Pearson correlation coefficient for p1 and p2
def sim_pearson(prefs,p1,p2):
    # Get the list of mutually rated items
    si={}
    for item in prefs[p1]:
        if item in prefs[p2]: si[item]=1
    # Find the number of elements
    n=len(si)
    # if they are no ratings in common, return 0
    if n==0: return 0
    # Add up all the preferences
    sum1=sum([prefs[p1][it] for it in si])
    sum2=sum([prefs[p2][it] for it in si])
    # Sum up the squares
    sum1Sq=sum([pow(prefs[p1][it],2) for it in si])
    sum2Sq=sum([pow(prefs[p2][it],2) for it in si])
    # Sum up the products
    pSum=sum([prefs[p1][it]*prefs[p2][it] for it in si])
    # Calculate Pearson score
    num=pSum-(sum1*sum2/n)
    den=sqrt((sum1Sq-pow(sum1,2)/n)*(sum2Sq-pow(sum2,2)/n))
    if den==0: return 0
    r=num/den
    return r

# Computes Jaccard similarity coefficient which is in [0,1]
# J(set1,set2) = intersection(set1,set2) / union(set1,set2)
def sim_jaccard(prefs,user1,user2):
    repos1 = prefs[user1]
    repos2 = prefs[user2]
    inter_len = len(repos1.intersection(repos2))
    union_len = float(len(repos1) + len(repos2) - inter_len)
    return inter_len / union_len

# Computes approximation to Jaccard similarity using precomputed MinHashes
# Pr[h_min(set1) == h_min(set2)] ~= J(set1,set2)
def sim_minhash(prefs, repo1, repo2, minhashes):
    hashes1 = minhashes[repo1]
    hashes2 = minhashes[repo2]
    same = 0
    for band1,band2 in zip(hashes1,hashes2):
        if band1 == band2: same += 1
    bands = minhash.num_hashes / minhash.num_per_band
    sim = same / float(bands)
    if sim > 0.0: print repo1,'<->',repo2,sim
    return sim

def transform_prefs(prefs):
    result=defaultdict(set)
    for (user,repos) in prefs.items():
        for repo in repos:
            # Add user to repo set
            result[repo].add(user)
    return dict(result)

# Returns the best matches for the keys of the prefs dictionary.
def top_matches(prefs, repo, n=5, similarity=sim_jaccard):
    # Get similarity scores for given repo
    scores = [
        (similarity(prefs,repo,repo2), repo2)
        for repo2 in prefs if repo!=repo2
    ]
    # Remove low similarity scores prior to sorting
    scores = [s for s in scores if s[0] > .05]

    # Sort by highest scores
    start_time = time.time()
    scores.sort(reverse=True)

    return scores[0:n]

def calculate_similar_repos(repo_prefs, n=10, minhashes=None):
    # TODO this should store similar repos in a db, or possibly need
    #      another function process_similar_items() that does MinHash
    # Create a dict showing repo similarity
    similar_repos = {}

    # Pull MinHashes from db
    if not minhashes:
        minhashes = dbutil.get_minhashes()

    for (count, repo) in enumerate(repo_prefs):
        # Status updates for large datasets
        if count%100==0 and count>0:
            print count, "/", len(repo_prefs)
        # Find the most similar repos to this one
        sim = partial(sim_minhash, minhashes=minhashes)
        scores = top_matches(repo_prefs, repo, n, sim)
        similar_repos[repo] = scores
    return similar_repos

def get_recommended_repos(prefs, repo_matches, user):
    user_starred = prefs[user]
    scores = defaultdict(lambda:0)
    count  = defaultdict(lambda:0)
    # Loop over repos starred by this user
    for repo in user_starred:
        # Loop over repos similar to this one
        for (similarity,repo2) in repo_matches[repo]:
            # Ignore if this user has already starred this item
            if repo2 in user_starred: continue
            # Sum similarity and increment count
            scores[repo2] += similarity
            count[repo2] += 1
    # Get list of repo-to-score tuples normalized by count of similarities
    rankings = [(score/count[repo],repo) for repo,score in scores.items()]
    # Return the rankings from highest to lowest
    rankings.sort(reverse=True)
    return rankings

if __name__ == '__main__':
    print "Beginning to calculate Github repository recommendations"
    print "======================================"

    print "Parsing data into Python from MongoDB dump"
    users_to_starred_repos = parse_user_to_repos_json()
    print "======================================"

    print "Calculating and saving MinHash values"
    repos_to_starred_repos = transform_prefs(users_to_starred_repos)
    hashes = minhash.generate_minhash(
        users_to_starred_repos, 
        repos_to_starred_repos.keys(),
    )
    print "======================================"

    print "Calculating which repositories are similar to one another"
    similar_repos = calculate_similar_repos(users_to_starred_repos)
