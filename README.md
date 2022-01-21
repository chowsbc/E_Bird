To see this app in action right now, see the demo video: https://drive.google.com/file/d/1lwv_Kn8UtgDEAtTLdn9unsso43cnoexH/view?usp=sharing

SPECIAL REQUIREMENTS
The main file you will interact with is 507FINAL.py. To use this file, you will need:

1) states.json (provided in the repository)
2) secrets.py, which should contain API keys for the LocationIQ API and the Cornell Ebird 2.0 API. For your convenience,
my Location IQ key is: 67e74a2012946f and my Ebird key is: hpl7psbh0k75. If you’d like to get your own keys, create
accounts at
-Location IQ: https://locationiq.com/register
-Cornell Lab: https://secure.birds.cornell.edu/cassso/login?service=https%3A%2F%2Febird.org%2Flogin%2Fcas%3Fportal%3Debird&locale=en_US.

Make sure to indicate that you’re using the Location IQ API for reverse geocoding when provided the option. The free
account is sufficient. Once you have your keys, you will need to create a Python file with the exact name “secrets.py”. This
file will need to have the code:

ebirdkey = '{{{your key for Cornell Ebird 2.0}}}'

liqkey = '{{{your key for Location IQ API}}}'

Put secrets.py in the same directory as 507FINAL.py and states.json.

REQUIRED PYTHON PACKAGES
1) requests
2) bs4
3) plotly
4) datetime.

All other packages are in the Python library.


INSTRUCTIONS
1)	Upon starting 507FINAL.py, you will be prompted to enter the name of a state that you wish to query. Enter the name
of a state and hit the “Enter” key. State names are not case sensitive. In this and all following instances in which you
are prompted for input, you may alternatively enter “exit” to stop the program.
2)	You will be presented with a numbered list of counties in your Python console and prompted to choose one of the
counties from the list. Enter the integer that corresponds to the desired county and hit the “Enter” key.
3)	You will be presented with three infographics about the overall bird sightings in the chosen county. These
infographics will be opened in your default browser. You also will also be presented with a numbered list of bird
sightings in the console.
4)	Enter the integer of the bird sighting that you wish to learn more about and hit the “Enter” key. You will be
presented with a picture of a member of the sighted bird’s species and a table containing information about the species
and the address of the sighting. These infographics will be opened in your default browser.
5)	You will be prompted to enter another state name and can repeat the above process as much as you like.


CODE ATTRIBUTION FOR PLOTLY TABLE
An exceptionally large amount of code for the function: "create_taxonomy_table" (lines 606-634) was copied verbatim from
Plotly documentation and then tailored. Therefore, I provided an attribution.
https://plotly.com/python/table/
