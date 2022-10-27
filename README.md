# prizes_history

This repository contains the code used to scrape and parse the nobels nominations database.

## downNobelDB

This script will download all the nominations for the chemistry prizes from 1901 to 1971 into the directory `./temphtmldir`.\
run it with `bash downNobleDB`.

## parse.py

this file can parse the downloaded HTML files into structs containing all the information about the nominators/nominees and insert them
into a mongodb database.

Data example:

    `{"name": "Jean B Perrin",
    	"id": "7136",
    	"gender": "M",
    	"birth": "1870",
    	"death": "1942",
    	"profession": null,
    	"university": "Sorbonne",
    	"city": "Paris",
    	"state": null,
    	"country": "FRANCE (FR) ",
    	"winner": true,
    	"prizes": "P in 1926|"
    	"nobel": [
    		{
    			"type": "P",
    			"year": "1926",
    			"name": "Prize in Physics"
    		}
    	],
    	"nominations": {
    		"465": [
    			{
    				"year": "1926",
    				"type": "C"
    			}
    		],
    		...
    		"9458": [
    			{
    				"year": "1915",
    				"type": "C"
    			},
    			{
    				"year": "1922",
    				"type": "C"
    			}
    		]
    		},
    }`

run this script with `python parse.py <html_files_directory>`

the main method will also insert missing data into the database.

## relationship.py

this script will take the nominations of each nominee in the db and create a relationship with the corresponding nominator:
| first_nomin_y | last_nomin_y | n_nominations | nominator_NP | nominator_id | nominator_name | nominee_NP | nominee_id | nominee_name |
|---------------|--------------|---------------|--------------|--------------|--------------------|-------------|------------|---------------|
| 1920 | 1924 | 2 | C in 1903\| | 511 | Svante A Arrhenius | P in 1926\| | 7136 | Jean B Perrin |

after running this script, the data can be exported into a csv from mongodb

## all_ch_people.csv

This file contains all the information parsed by the relationship.py script
