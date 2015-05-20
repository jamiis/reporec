NOTE: This is in a state of slight disrepair and the 
instructions below aren't guaranteed to work properly.

To run a demo of reporec run in your terminal

$ python reporec.py

There is unfortunately a dependency on mongo 
that I couldn't avoid :(

Because the full db is far too large to zip, and 
downloading from GHTorrent takes a very long time 
I am including a sample of the data as a json file 
that will be parsed into python in the main function 
of reporec.py. But minhash requires mongo.

To download and load into mongo the n most recent 
Watchers datasets, run

$ ./download_data n

where n is an integer. Each dataset is approx 2 months
of data.

You can also export the userToRepos data by running

$ ./export_user_to_repos.sh
