# exports userToRepos collection to .json file
mongoexport --db github --collection userToRepos --jsonArray --fields repos --out userToRepos.json
