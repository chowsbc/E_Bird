import requests
import json
import sqlite3
import secrets
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import datetime
import webbrowser

'''COMMENT'''

CACHE_FILE_NAME = "bird_cache.json"
DB_NAME = 'bird.sqlite'
CACHE_DICT = {}

def load_cache():
    '''
    Opens a cache dictionary of a specified name if it is in the active directory- otherwise creates a new cache dictionary.

    Attempts to open a json cache file of a name that is specified by global variable "CACHE_FILE_NAME". Converts the
    contents of the cache file into a dictionary and returns the dictionary. If the cache file of the specified name
    cannot be opened, creates an empty dictionary and returns it.

    Parameters
    ----------
    none

    Returns
    -------
    dict
        A dictionary that either contains the converted contents of the json cache file or is empty.
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        CACHE_DICT = json.loads(cache_file_contents)
        cache_file.close()

    except:
        CACHE_DICT = {}

    return CACHE_DICT


def save_cache(cache):
    ''' Opens a json cache file of a globally specified name and writes the cache dictionary to the cache file.

    Opens a json cache file of a name that is specified by local variable "CACHE_FILE_NAME". Writes the contents of the
    cache dictionary to the cache file.

    Parameters
    ----------
    cache: dict
        Contains the contents to be saved to the cache file.

    Returns
    -------
    none
    '''
    # t = type(cache)

    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache):
    ''' Uses a url to search the cache dictionary or alternatively, the internet, for html content. Saves the content.

        Looks for a key-value pair in the cache dictionary with a key that is identical to a url. If such a key-value
        pair is located, returns the value from the key-value pair. If not, gets HTML content from the internet
        from the address indicated by the url. Converts the HTML to text. Adds a key-value pair to the dictionary
        where the key is the url and the value is the HTML content. Saves the cache dictionary to a json file.

        Parameters
        ----------
        url: string
           The url that is used to search the cache dictionary or the internet

        cache: dict
            A dictionary containing content that has been acquired from the internet.

        Returns
        -------
        string
            The value from the cache dictionary that corosponds to the url key.
        '''
    if (url in cache.keys()):
        print("\nUsing cache")
        return cache[url]

    else:
        print("\nFetching")
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)

        return cache[url]


def create_tables():
    '''Deletes counties and sightings sqlite tables if they exist, then creates the counties and sightings tables.

        Checks to see if the tables "counties" and "sightings" exist in the sqlite database specified by
        "DB_NAME" (bird.sqlite). If they do, drops these tables. Then, creates the counties and sightings tables.

        Parameters
        ----------
        none

        Returns
        -------
        None (But creates a counties table and sightings table)'''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    create_counties_sql = '''
        CREATE TABLE IF NOT EXISTS "counties" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "state_count" INTEGER NOT NULL,
            "Location_Code" TEXT NOT NULL,
            "County" TEXT NOT NULL,
            UNIQUE(Location_Code, County)
        )
    '''
    create_sightings_sql = '''
        CREATE TABLE IF NOT EXISTS "sightings" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "County_Name" TEXT NOT NULL,
            "County_Index" TEXT NOT NULL,
            "Species_Code" TEXT NOT NULL,
            "Common_Name" TEXT NOT NULL,
            "Scientific_Name" TEXT NOT NULL,
            "Location_Name" TEXT,
            "Observation_Date" TEXT,
            "Lat" TEXT NOT NULL,
            "Long" TEXT NOT NULL,
            "PrivateLocation" TEXT NOT NULL

        )
    '''
    drop_counties = '''
        DROP TABLE IF EXISTS "counties";
    '''
    drop_sightings = '''
        DROP TABLE IF EXISTS "sightings";
    '''
    cur.execute(drop_counties)
    cur.execute(drop_sightings)
    cur.execute(create_counties_sql)
    cur.execute(create_sightings_sql)
    conn.commit()
    conn.close()
    pass

def check_input(query, maximum, domain, action):
    '''Checks if variable, "query" is a string version of an integer. If not, prompts user for input until this is satisfied. If "query" is ever "exit", quits the program.

    Checks if variable "query" is "exit", and exits the program if so. If not, checks if query has any non-numeric
    characters, has any decimal points, or is outside the range of 1 to "maximum". If any of these are true,
    prompts the user for valid input and checks the input again. When the user has entered valid input (A string
    version of an integer), the corrected "query" (or the "query" that was correct on the first try) is returned.

    parameters:
    ---------
    query: string
        The query made by the user.

    maximum: int
        The maximum value that the integer version of the user's query should have.

    domain: string
        A word indicating what kind of item the user is choosing (either "bird" or "county").

    action: string
        A phrase indicating what the user would accomplish by making their query.

    returns:
    -------
    Query: string
        The valid query made by the user, either after entering a valid query at the first attempt or after satisfying
        a prompt for a correct query.
    '''
    while True:
        if query == "exit":
            exit()
        if query.isnumeric():
            if "." in query or "." in str(query):
                query = input('Please choose a valid integer for the ' + domain + ' you would like to ' + action + ' or "exit":')
                continue
            if int(query) < 1 or int(query) > maximum:
                query = input('Please choose a valid integer for the ' + domain + ' you would like to ' + action + ' or "exit":')
                continue
            else:
                break
        else:
            query = input('Please choose a valid integer for the ' + domain + ' you would like to ' + action + ' or "exit":')
            continue
    return query


def populate_counties_DB(state_short, birdkey=secrets.ebirdkey):
    '''Uses a state abreviation to query the Ebird API for data on the state's counties and adds the data to bird.sqlite.

    Uses an abbreviation of a state (state_short) to assemble a query to the "Get Region Info" endpoint of the Ebird API.
    Query returns a list of dictionaries about each county in the state. Each county dictionary contains the county's name
    and a specific county code. Writes this information into the counties table of the the sqlite database specified by the
    global variable "DB_NAME" (bird.sqlite)

    Parameters:
    ----------
    state_short: string
        The abbrevation of the state that the user indicated they would like to query.

    birdkey: string
        An API key that must be included in the query to use the Ebird 2.0 API.

    Returns:
    ------
    None (But adds data to the counties database)
        '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    insert_counties_sql = '''
            INSERT INTO counties
            VALUES (NULL, ?, ?, ?)

        '''

    state_code = 'US-' + state_short
    url1 = 'https://api.ebird.org/v2/ref/region/list/subnational2/' + state_code + '?key=' + birdkey
    area_list = make_url_request_using_cache(url1, CACHE_DICT)
    sample_area_json = json.loads(area_list)
    count = 0
    for item in sample_area_json:
        count += 1
        try:
            cur.execute(insert_counties_sql,
                        [
                            count,
                            item['code'],
                            item['name'],
                        ]
                        )
        except:
            pass
    conn.commit()
    conn.close()
    pass

def populate_sightings_DB(county_choice, state_short, birdkey=secrets.ebirdkey):
    '''Retrieves a county code and county name from bird.sqilte and uses the code to query sightings info and add it to bird.sqlite.

    Uses county_choice and state_short (a state abbreviation) to assemble a query to the sqlite database specified by
    "DB_NAME". (bird.sqlite). The query returns a list with one tuple about a particular county. Parses a county code
    and county name from the tuple and uses it to assemble a query to the "Get Recent Observations" endpoint of the
    eBird 2.0 API. Retrieves information about recent bird sightings and adds it to bird.sqlite. Returns county_name
    (the name of the county represented by county_choice).

    Parameters:
    ----------
    county_choice: string
        A number in string format. This number represents the county choice that the user made when asked what county
        they wish to query.

    state_short: string
        A state abbreviation. This abbreviation represents the state choice that the user made when asked what state
        they wish to query.

    birdkey: string
        An API key that must be included in the query to use the Ebird 2.0 API.

    Returns:
    -------
    county_name: string
        The name of the county retrieved from the sqlite query.
        '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    result = cur.execute(
        "select Location_Code, County from counties where state_count = " + county_choice + " and Location_Code like '%" + state_short + "%';").fetchall()
    county_code = result[0][0]
    county_name = result[0][1]
    url = 'https://api.ebird.org/v2/data/obs/' + county_code + '/recent' + '?key=' + birdkey
    print('\nFetching\n')
    response = requests.get(url)
    response_text = response.text
    sightings_json = json.loads(response_text)

    insert_sightings_sql = '''
                INSERT INTO sightings
                VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            '''
    county_index = 0
    id_list = cur.execute("select Id from sightings where County_Name = '" + county_name + "'").fetchall()
    if len(id_list) == 0:
        for item in sightings_json:
            county_index += 1
            cur.execute(insert_sightings_sql,
                        [
                            county_name,
                            county_index,
                            item['speciesCode'],
                            item['comName'],
                            item['sciName'],
                            item['locName'],
                            item['obsDt'],
                            item['lat'],
                            item['lng'],
                            item['locationPrivate']
                        ]
                        )
    else:
        pass
    conn.commit()
    conn.close()
    return county_name

def create_county_list(state_short, state_name):
    '''Queries bird.sqlite for information about the counties in a state. Prints a numbered list of counties.

    Uses a state abbreivation (state_short) to create a query to the sqlite database specified by the global variable
    "DB_NAME" (bird.sqlite). Query returns a list of tuples containing data about the counties in the state. Uses this
    information to print a numbered list of counties. Uses state_name to create a label for the list. Returns
    county_count- an integer equal to the number of counties represented in the query result.

    Parameters:
    ----------
    state_short: string
        The abbrevation of the state that the user indicated that they would like to query.

    state_name: string
        The name of the state that the user indicated that they would like to query.

    Returns:
    --------
    county_count: int
        The number of counties represented in the data returned by the query.
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    result = cur.execute("select Id, state_count, Location_Code, County from counties where Location_Code like '%" + state_short + "%';").fetchall()
    print('\nLIST OF COUNTIES IN ' + state_name.upper())
    county_count = 0
    for item in result:
        print("[" + str(item[1]) + "] " + item[3])
        county_count = item[1]
    return county_count

def create_sightings_list(county_name):
    '''Queries bird.sqlite for information about recent bird sightings in a county. Prints a numbered list of bird sightings.

    Uses county_name to create a query to the sqlite database specified by the global variable "DB_NAME" (bird.sqlite).
    Query returns a list of tuples containing data about the recent bird sightings in the county. Uses this information
    to print a numbered list of bird sightings.

    Parameters:
    ----------
    county_name: string
        The name of a county.

    Returns:
     --------
    sighting_count: int
        The number of sightings represented in the data returned by the query.
    '''
    sighting_count = 0
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    result = cur.execute('select County_Index, Common_Name, Scientific_Name, Location_Name, Observation_Date from sightings where County_Name = "' + county_name + '"').fetchall()

    print('LIST OF BIRD SIGHTINGS IN ' + county_name.upper())

    for item in result:
        print("[" + str(item[0]) + "] Species: " + item[1] + " | Date: " + item[4])
        sighting_count = item[0]
    return int(sighting_count)

def reverse_geocode(sighting_choice, county_name, liqkey=secrets.liqkey):
    '''Uses an integer that represents a bird sighting queried by the user, and the name of the county of the bird sighting, to return the address of the sighting.

    Uses an integer representing the bird sighting that the user chose to query (sighting_choice) and the name of a
    county (county_name) to assemble a query to the Location IQ API. The query contains a dictionary with address
    information about the sighting. "display_name" is parsed from the dictionary and returned as address_response.

    parameters:
    ----------
    sighting_choice: int
        An integer representing the bird sighting that the user chose to query.

    county_name: string
        The county that the user chose to query.

    liqkey: string
        An API key that must be included in the query to use the Location IQ API.


    returns:
    -------
    address_response: string
        A string representing the address of the bird siting that the user queried.
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    result = cur.execute('select Lat, Long from sightings where County_Index = ' + sighting_choice + ' and County_Name = "' + county_name + '";').fetchall()
    url3 = 'https://us1.locationiq.com/v1/reverse.php?key=' + liqkey + '&lat=' + str(result[0][0]) + '&lon=' + str(
        result[0][1]) + '&format=json'
    address_parent_response = make_url_request_using_cache(url3, CACHE_DICT)
    address_parent_json = json.loads(address_parent_response)
    address_response = address_parent_json["display_name"]
    return address_response

def scrape_species_page(sighting_choice, county_name):
    '''Uses the user's bird sighting choice, and the name of the county that they queried, to find the page about the sighted bird's species on Birds.Cornell.edu. Returns information about the species in a dictionary.

    Uses the string version of an integer representing the bird sighting that the user queried (sighting_choice) and
    county_name to create a query to the sqlite database specified by the global variable "DB_NAME" (bird.sqlite). Query
    returns a species code, which is used to create a url. The url is requested and the returned html is scraped for
    information about the sighted bird's species, which includes an image url, the specie's taxonomic information, and
    its status (eg. "endangered"). This information is used create a dictionary, which is returned.

    parameters:
    ----------
    sighting_choice: string
        A string version of an integer representing the bird sighting that the user chose to query.

    county_name: string
        The county that the user chose to query.


    returns:
    -------
        species_page_data: dictionary
        Contains key value pairs representing a bird specie's status, and its taxonomic classification. Also has an image url.
    '''
    species_page_data = {'img_url': '', 'status': '', 'taxonomy': ''}
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    species_code_response = cur.execute(
        'select Species_Code from sightings where County_Index = ' + sighting_choice + ' and County_Name = "' + county_name + '";').fetchall()
    species_code_parsed = species_code_response[0][0]
    species_url = 'https://birdsna.org/Species-Account/bna/species/' + str(species_code_parsed) + '/introduction'
    homepage_dict = make_url_request_using_cache(species_url, CACHE_DICT)
    homepage_soup = BeautifulSoup(homepage_dict, 'html.parser')

    pic_block = homepage_soup.find('div', class_='AspectRatioContent')
    pic_parent = pic_block.find('img')
    pic_url = pic_parent['src']
    species_page_data['img_url'] = pic_url

    badge = ''
    badge_parent = homepage_soup.find('div', class_='u-text-3 Tooltip Tooltip--sm')
    if badge_parent == None:
        badge = 'Status not listed'
    else:
        pre_badge = (badge_parent.text).split()
        badge_parts = pre_badge[1:]
        for part in badge_parts:
            badge += part + ' '
    species_page_data['status'] = badge

    taxonomy_dict = {1: '', 2: '', 3: ''}
    order_parent = homepage_soup.find('div', class_='Toolbar-group Toolbar-group--secondary')
    toolbar_items = order_parent.find_all('div', class_='Toolbar-item')
    taxonomy_index = 0
    for item in toolbar_items:
        taxonomy_index += 1
        classification = item.text.strip()
        taxonomy_dict[taxonomy_index] = classification

    species_page_data['taxonomy'] = taxonomy_dict
    return species_page_data

def create_locations_chart(county_name):
    '''Queries bird.sqlite for data about the locations with the 5 greatest amounts of sightings in a particular county and creates a scatterplot.

    Uses county_name to create a query to the sqlite database specified by the global variable "DB_NAME" (bird.sqlite).
    Query retrieves a list of tuples of the observation dates of all the county's recent bird sightings.
    Creates a list of unique dates and a corrosponding list of amounts of bird sightings associated with those dates.
    Uses Plotly to create a scatter plot showing the number of recent bird sightings per day across the last several
    days and opens it on the user's browser. Returns "result"- which is the list of dictionaries returned by the query.

    Parameters:
    ----------
    county_name: string
        The name of a county.

    Returns:
    --------
    None (but creates a Plotly infogrpahic and opens it on the user's browser.)
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    result = cur.execute(
        'SELECT Location_Name, Lat, Long, PrivateLocation, COUNT(Location_Name) FROM sightings WHERE County_Name = "' + county_name + '" GROUP BY Location_Name ORDER BY Count(Location_Name) DESC LIMIT 5').fetchall()
    x_axis = []
    y_axis = []
    for location in result:
        x_axis.append(int(location[4]))
        y_string = location[0] + '  |  ' + 'lat: ' + str(location[1]) + ' / ' + 'long: ' + str(location[2] + '    ')
        y_axis.append(y_string)
    basic_layout = go.Layout(title="Recent Bird Sightings in " + county_name + " County")
    fig = go.Figure(go.Bar(x=x_axis, y=y_axis, orientation='h'), layout=basic_layout)
    fig.write_html("locationchart.html", auto_open=True)

    conn.close()
    return result

def create_sightings_scatterplot(county_name):
    '''Queries bird.sqlite for dates of recent sightings in a particular county and creates a scatter plot.

    Uses county_name to create a query to the sqlite database specified by the global variable "DB_NAME" (bird.qlite).
    Query retrieves a list of tuples of the observation dates of all the county's recent bird sightings.
    Creates a list of unique dates and a corrosponding list of amounts of bird sightings associated with those dates.
    Uses Plotly to create a scatter plot showing the number of recent bird sightings per day across the last several
    days and opens it on the user's browser.

    Parameters:
    ----------
    county_name: string
        The name of a county.

    Returns:
    --------
    None (but creates a Plotly infogrpahic and opens it on the user's browser.)'''
    date_hist = {}
    unique_dates = []
    y_axis_list = []
    x_axis_list = []
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    result = cur.execute('select Observation_Date from sightings where County_Name = "' + county_name + '" ORDER BY Observation_Date ASC;').fetchall()

    for date_tuple in result:
        date_parsed = date_tuple[0].split()[0]
        if date_parsed in date_hist:
            date_hist[date_parsed] += 1
        else:
            date_hist[date_parsed] = 1
        if date_parsed in unique_dates:
            pass
        else:
            unique_dates.append(date_parsed)
    for date in unique_dates:
        date_count = date_hist[date]
        y_axis_list.append(date_count)
        date_parts = date.split('-')
        x_axis_list.append(datetime.datetime(year=int(date_parts[0]), month=int(date_parts[1]), day=int(date_parts[2])))

    basic_layout = go.Layout(title="Recent Bird Sightings in " + county_name + " County")
    fig = go.Figure(data=[go.Scatter(x=x_axis_list, y=y_axis_list)], layout=basic_layout)
    fig.write_html("linegraph.html", auto_open=True)
    pass

def create_private_pie(county_name):
    '''Queries birds.sqlite for the numbers of recent bird sightings on private and on public property in a county. Creates a pie chart.

    Uses county_name to create two queries to the sqlite database specified by the global variable "DB_NAME" (bird.sqlite).
    One query returns a list of one tuple with the number of recent bird sightings on public property. The other
    query returns a list of one tuple with the number of recent bird sightings on private property. Uses Plotly to make
    a pie chart with the percentage of bird sightings on public and on private property and opens them in the user's browser.

    Parameters:
    ----------
    county_name: string
        The name of a county.

    Returns:
    --------
    None (but creates a Plotly infogrpahic and opens it in the user's browser.)
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    Private_Count = cur.execute('SELECT COUNT(PrivateLocation) from sightings WHERE PrivateLocation = 1 and County_Name = "' + county_name + '"').fetchall()
    Public_Count = cur.execute('SELECT COUNT(PrivateLocation) from sightings WHERE PrivateLocation = 0 and County_Name = "' + county_name + '"').fetchall()
    labels = ['Private Property', 'Public Property']
    values = [Private_Count[0][0], Public_Count[0][0]]


    basic_layout = go.Layout(title="Proportions of Sightings in Public and Private Property in " + county_name)
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)], layout = basic_layout)
    fig.write_html("pirivatepublicchart.html", auto_open=True)

def create_taxonomy_table(species_page_data, address):
    '''Parses data from species_page_data and uses it to create a table presenting the data. Also displays address data in the table.

    From species_page_data_, parses the order, family, genus, and status (eg. "endangered"), of a bird that was sighted,
    as well as the address that it was sighted at. Uses Plotly to create a table that displays this information.

    Parameters:
    ----------
    species_page_data: dictionary
        Contains key value pairs representing a bird specie's status, and its taxonomic classification. Also has an image url.

    address: string
        A string representing the address of a bird siting that the user has queried.

    Returns:
    --------
    None (but creates a Plotly infographic and opens it on the user's browser.)
    '''
    values = [["Order", "Family", "Genus", "Status", "Address Sighted"],
              [ species_page_data["taxonomy"][1],
                species_page_data["taxonomy"][2],
                species_page_data["taxonomy"][3],
                species_page_data['status'],
                address]]

    fig = go.Figure(data=[go.Table(
        columnorder=[1, 2],
        columnwidth=[80, 400],
        header=dict(
            values=[['<b>Information Types</b>'],
                    ['<b>Information</b>']],
            line_color='darkslategray',
            fill_color='royalblue',
            align=['left', 'center'],
            font=dict(color='white', size=12),
            height=40
        ),
        cells=dict(
            values=values,
            line_color='darkslategray',
            fill=dict(color=['paleturquoise', 'white']),
            align=['left', 'center'],
            font_size=12,
            height=30)
    )
    ])
    fig.write_html("taxonomychart.html", auto_open=True)

if __name__ == "__main__":
    create_tables()
    firstquery = True
    CACHE_DICT = load_cache()
    state_json = open('statelist.json', 'r')
    states = json.load(state_json)
    if firstquery == True:
        state = input('\nWelcome! To get started searching for bird sitings info, enter the name of the state you would like to query, or "exit": ')
    while True:
        if firstquery == False:
            state = input('To search for more bird sitings, enter the name of the state you would like to query, or enter "exit":')
            if state == "exit":
                break
        if state == "exit":
            exit()
        else:
            if state.lower() in states:
                state_short = states[state.lower()]
                firstquery = False
            else:
                while True:
                    state = input("Please enter a valid state:")
                    if state.lower() in states:
                        state_short = states[state.lower()]
                        firstquery = False
                        break
                    elif state == "exit":
                        exit()
                    else:
                        pass

            populate_counties_DB(state_short)
            county_max = create_county_list(state_short, state)
            county_choice = input('\nSelect the integer of the county you would like to query, or "exit": ')
            county_choice = check_input(county_choice, county_max, "county", "query")
            county_name = populate_sightings_DB(county_choice, state_short)
            sighting_max = create_sightings_list(county_name)
            if sighting_max > 0:
                create_locations_chart(county_name)
                create_sightings_scatterplot(county_name)
                create_private_pie(county_name)
                sighting_choice = input(
                    '\nRelevant items have been opened in your deafult browser.\n-----\nSelect the integer of the bird sighting you would like to learn more about, "exit": ')
                sighting_choice = check_input(sighting_choice, sighting_max, "bird sighting", "learn more about")
                address_response = reverse_geocode(sighting_choice, county_name)
                try:
                    species_page_data = scrape_species_page(sighting_choice, county_name)
                    bird_pic = species_page_data['img_url']
                    webbrowser.open(bird_pic)
                    create_taxonomy_table(species_page_data, address_response)
                    print('\nRelevant items have been opened in your default browser.\n-----\n')
                except:
                    print("\nSorry! This specie's eBird page follows an unstandard format and we could not retrieve details.")
            else:
                print('\nSorry! This area has no reported sightings.')


