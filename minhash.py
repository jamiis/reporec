import sys, time
from random import randint

from dbutil import db
 
num_hashes = 10
num_per_band = 2
  
def minhash(a, b, signature, item_ids):
    hashes = []
    for x in signature:
        _hash = ((a * x) + b) % len(item_ids)
        hashes.append(_hash)
    return min(hashes)

def minhash_row(sig, item_ids):
    a_hashes = [randint(0,sys.maxint) for _ in xrange(0, num_hashes)]
    b_hashes = [randint(0,sys.maxint) for _ in xrange(0, num_hashes)]
 
    hashes = []
    for a,b in zip(a_hashes, b_hashes):
        _hash = minhash(a, b, sig, item_ids)
        hashes.append(_hash)
    return hashes
 
def get_band(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]
 
# Generate dictionary of repo-name to unique-id
def generate_item_ids(items):
    return dict((item,idx) for idx,item in enumerate(items))
 
# Generate minhashes of lists of items for preferences dict.
# Typically preferences dict is repo-to-users but could be opposite.
def generate_minhash(prefs, items, key="repo", store=True):
    print "MinHash on ",key,". Total matrix size: ",len(prefs)," x ",len(items)
    start_time = time.time()
    count = 0

    hashes = {}
    item_ids = generate_item_ids(items)

    for (pref,items) in prefs.items():
        # Track progress
        if count%1000==0 and count>0:
            print "iteration %d / %d" % (count,len(prefs))
        count += 1

        signature = [item_ids[item] for item in items]
        minhashes = minhash_row(signature, item_ids) 
        banded = get_band(minhashes, num_per_band)

        if store:
            # Save banded minhashes to mongo
            db.minhash.update(
                { key: pref },
                { 
                    key: pref,
                    'hashes': banded,
                },
                upsert=True,
            )
        else:
            # Add to results dictionary
            hashes[pref] = banded

    print "Runtime MinHash:", time.time()-start_time

    if not store:
        return hashes

