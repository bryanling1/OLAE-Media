# Ontario League of Associated Esports - Media and Helper Functions

The [Ontario League of Associated Esports (OLAE)](https://olae.ca) is a varsity League of Legends league based in Ontario Canada. 

This Python class assists in the generation of [social media content](https://www.instagram.com/olae.ca/), as well as Firebase queries. 

Firebase database permissions are required. 

<p align="center">
    <img alt="olae-site-preview1" title="olae-site-preview1" src="https://olae.ca/images/news/1-1-2020-smPreview.png" width="100%">
</p> 

## Build Instructions
1. Install [Pyrebase](https://github.com/thisbejim/Pyrebase)
2. Install [PIL](https://pypi.org/project/Pillow/2.2.2/)
3. Install [Moviepy](https://zulko.github.io/moviepy/install.html)
4. Create a fbKey.json file in the main directory with Firebase service account info 
5. `instance = Olae()` and use defined methods in the class as needed

## Usage
Methods are written to be used in the console as some require additional user inputs.


```python
olae = Olae() #initialize

olae.addUsersFromSpreadsheet(event, password)
"""
From the given spreadsheet templates in the OLAE 
Startup Package, identify new users and set the initial password
:param event: event name
:type event: str
:param password: initial account passwords
:type password: str
"""
olae.genRegularSeasonMatches(event, matches, year, month, day, time)
"""
Generate regular season matches and query to Firebase based on registered teams
:param event: event name
:type event: str
:param matches: number of match days
:type matches: int
:param year: start date year
:type year: int
:param month: start date month
:type month: int
:param day: start date day
:type day: int
:param time: start time string
:type time: str
"""
olae.createScheduleImages(event)
"""
Generate matchup images
:param event: event name
:type event: str
"""
olae.createRosterImages(event)
"""
Generate roster images
:param event: event name
:type event: str
"""
olae.createMatchResultImages(event)
"""
Generate match results images. Requires additional user input
:param event: event name
:type event: str
"""
olae.createStatImages(event)
"""
Generate stat images for a given week. Requires additional user input
:param event: event name
:type event: str
"""
olae.createMog()
"""
Generate Moments of Glory clips. Requires additional user input
"""
```
**Note:** Some video overlay assets have not been included due to large file sizes. Issues with video masking occured with PIL and .avi files with transparency were used instead.

## Feedback

Feel free to [file an issue](https://github.com/bryanling1/OLAE-website/issues/new).
## Contributing
Please open an issue first to discuss what you would like to change.

