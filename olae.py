import pyrebase
import csv
import random
import operator
from datetime import date
from datetime import timedelta
from datetime import datetime
from os import makedirs
from os import listdir
from os.path import isfile, join
from termcolor import colored
from colored import fg, stylize
from collections import deque
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from PIL import ImageEnhance
from urllib import request
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx, CompositeVideoClip, TextClip, ImageClip


class Olae:
    def __init__(self):
        self.config = {
            'apiKey': "AIzaSyCGsKsCmcbwWtl7FIPkwv6Hc9PGwQxJggs",
            'authDomain': "olae-d3d90.firebaseapp.com",
            'databaseURL': "https://olae-d3d90.firebaseio.com",
            'projectId': "olae-d3d90",
            'storageBucket': "olae-d3d90.appspot.com",
            'messagingSenderId': "65901038805",
            'serviceAccount': './fbKey.json'
        }
        self.firebase = pyrebase.initialize_app(self.config)
        self.db = self.firebase.database()

    def create_balanced_round_robin(self, players, matches):
        """ Create a schedule for the players in the list and return it"""
        s = []
        if len(players) % 2 == 1: players = players + [None]
        # manipulate map (array of indexes for list) instead of list itself
        # this takes advantage of even/odd indexes to determine home vs. away
        n = len(players)
        map = list(range(n))
        mid = n // 2
        for i in range(matches):
            l1 = map[:mid]
            l2 = map[mid:]
            l2.reverse()
            round = []
            for j in range(mid):
                t1 = players[l1[j]]
                t2 = players[l2[j]]
                if j == 0 and i % 2 == 1:
                    # flip the first match only, every other round
                    # (this is because the first match always involves the last player in the list)
                    round.append((t2, t1))
                else:
                    round.append((t1, t2))
            s.append(round)
            # rotate list by n/2, leaving last element at the end
            map = map[mid:-1] + map[:mid] + map[-1:]
        return s

    


    def addUsersTableToEventFromAllUsers(self, event):
        all_users = self.db.child("users").get()
        return_data = {}
        for user in all_users.each():
            if(user.val()['event'] == event):
                return_data[user.key()] = {}
                return_data[user.key()]['team'] = user.val()['team']
                return_data[user.key()]['firstName'] = user.val()['firstName']
                return_data[user.key()]['lastName'] = user.val()['lastName']
                return_data[user.key()]['summoner'] = user.val()['summoner']
                return_data[user.key()]['username'] = user.val()['username']
        self.db.child('liveEvents/'+event+'/users').set(return_data)

    def addTeamsTableToEventFromAllUsers(self, event):
        all_users = self.db.child("users").get()
        return_data = {}
        for user in all_users.each():
            if(user.val()['event'] == event):
                if user.val()['team'] not in return_data:
                    return_data[user.val()['team']] = {}
                return_data[user.val()['team']][user.key()] = {}
                return_data[user.val()['team']][user.key()]['firstName'] = user.val()['firstName']
                return_data[user.val()['team']][user.key()]['lastName'] = user.val()['lastName']
                return_data[user.val()['team']][user.key()]['summoner'] = user.val()['summoner']
                return_data[user.val()['team']][user.key()]['username'] = user.val()['username']
                return_data[user.val()['team']][user.key()]['status'] = 'offline'
        self.db.child('liveEvents/'+event+'/teams').set(return_data)
    
    #credit to https://gist.github.com/ih84ds/be485a92f334c293ce4f1c84bfba54c9
    def genRegularSeasonMatches(self, event, matches, year, month, day, time):
        db_teams = self.db.child('liveEvents/'+event+'/teams').get()
        teams = []
        return_data = {}
        for team in db_teams.each():
            teams.append(team.key())
        random.shuffle(teams)

        schedule = self.create_balanced_round_robin(teams, matches)
        start = date(year, month, day)
        # print("\n".join(['{} vs. {}'.format(m[0], m[1]) for round in schedule for m in round]))
        for day in schedule:
            for m in day:
                if(m[0] != None and m[1] != None):
                    ref = self.db.child('liveEvents/'+event+"/matches")
                    new_key = ref.generate_key()
                    return_data['liveEvents/'+event+"/matches/"+new_key+"/blueTeam"] = m[0] 
                    return_data['liveEvents/'+event+"/matches/"+new_key+"/redTeam"] = m[1] 
                    return_data['liveEvents/'+event+"/matches/"+new_key+"/nextMatch"] = False
                    return_data['liveEvents/'+event+"/matches/"+new_key+"/date"] = (str(start)+"T"+time)
                    return_data['liveEvents/'+event+"/teamMatches/"+m[0]+"/"+new_key+"/blueTeam"] = m[0] 
                    return_data['liveEvents/'+event+"/teamMatches/"+m[0]+"/"+new_key+"/redTeam"] = m[1] 
                    return_data['liveEvents/'+event+"/teamMatches/"+m[0]+"/"+new_key+"/nextMatch"] = False
                    return_data['liveEvents/'+event+"/teamMatches/"+m[0]+"/"+new_key+"/date"] = (str(start)+"T"+time)
                    return_data['liveEvents/'+event+"/teamMatches/"+m[1]+"/"+new_key+"/blueTeam"] = m[0] 
                    return_data['liveEvents/'+event+"/teamMatches/"+m[1]+"/"+new_key+"/redTeam"] = m[1] 
                    return_data['liveEvents/'+event+"/teamMatches/"+m[1]+"/"+new_key+"/nextMatch"] = False
                    return_data['liveEvents/'+event+"/teamMatches/"+m[1]+"/"+new_key+"/date"] = (str(start)+"T"+time)
            start += timedelta(days=7)
        try:
            self.db = self.firebase.database()
            self.db.update(return_data)
            print(colored('Succesfully Added Matches', 'green'))
        except:
            print(colored("Failed to add matches", 'red'))
        
    def addUsersFromSpreadsheet(self, event, password):
        #remember to names the file as the team name
        return_data = []
        row_data = [{}] * 10
        rosters_path = './rosters/'
        ss_files = [f for f in listdir(rosters_path) if isfile(join(rosters_path, f))]
        for file in ss_files:
            with open(rosters_path+file) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                for row in csv_reader:
                    if (line_count - 2) % 4 == 0:  
                        for data in row_data:
                            if 'firstName' in data and data['firstName'] != '' and data['lastName']!= '' and data['email']!= '' and data['summoner']!= '':
                                return_data.append(data)
                                
                        row_data = [{}] * 8
                        for i in range(2, 10):
                            row_data[i-2] = {}
                            if len(row[i].split(" ")[0]) > 1:
                                row_data[i-2]['firstName'] = row[i].split(" ")[0][0].upper() + row[i].split(" ")[0][1:].lower()
                            else:
                                row[i].split(" ")[0].upper()
                            
                            if len(" ".join(row[i].split(" ")[1:] )) > 1:   
                                row_data[i-2]['lastName'] = (" ".join(row[i].split(" ")[1:]))[0].upper() + (" ".join(row[i].split(" ")[1:]))[1:].lower()
                            else:
                                row_data[i-2]['lastName'] = " ".join(row[i].split(" ")[1:])

                            row_data[i-2]['event'] = event
                            row_data[i-2]['team'] = file[:-4]+"-"+str(int((line_count - 2)/4+1))
                    if (line_count - 3) % 4 == 0:
                        for i in range(2, 10):
                            row_data[i-2]['email'] = row[i]
                    if (line_count - 4) % 4 == 0:
                        for i in range(2, 10):
                            row_data[i-2]['summoner'] = row[i]

                    line_count += 1
            csv_file.close()
        #loop through the users in teh spreadsheet
        auth = self.firebase.auth()
        users = self.db.child('users').get()
        new_users_data = {}
        all_users_from_db = {}
        new_teams = []
        old_teams = []
        #lets get all the teamData to see what new teams have to be created
        teamData_db = self.db.child("teamData").get()
        for team in teamData_db.each():
            old_teams.append(team)
        #get all the users from the database because this program hates me
        users = self.db.child("users").get()
        for u in users.each():
            if 'email' in u.val():
                all_users_from_db[u.val()['email']] = u.val()
                all_users_from_db[u.val()['email']]['id'] = u.key()

        for data in return_data:
            if(data['team'].split("-")[0] not in old_teams):
                old_teams.append(data['team'].split("-")[0])
                new_teams.append(data['team'].split("-")[0])
            #update user data
            try:
                newUser = auth.create_user_with_email_and_password(data['email'].replace(" ", ""), password)
                localId = newUser['localId']
                new_users_data['users/'+localId+'/firstName'] = data['firstName']
                new_users_data['users/'+localId+'/lastName'] = data['lastName']
                new_users_data['users/'+localId+'/summoner'] = data['summoner']
                new_users_data['users/'+localId+'/username'] = data['summoner']
                new_users_data['users/'+localId+'/team'] = data['team']
                new_users_data['users/'+localId+'/event'] = data['event']
                new_users_data['users/'+localId+'/email'] = data['email'].replace(" ", "")
                #add to teams
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/firstName"] = data['firstName']
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/lastName"] = data['lastName']
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/summoner"] = data['summoner']
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/username"] = data['summoner']
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/status"] = 'offline'
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/wins"] = 0
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/losses"] = 0
                #add to event users list
                new_users_data['liveEvents/'+event+'/users/'+localId+"/firstName"] = data['firstName']
                new_users_data['liveEvents/'+event+'/users/'+localId+"/lastName"] = data['lastName']
                new_users_data['liveEvents/'+event+'/users/'+localId+"/summoner"] = data['summoner']
                new_users_data['liveEvents/'+event+'/users/'+localId+"/username"] = data['summoner']
                new_users_data['liveEvents/'+event+'/users/'+localId+"/team"] = data['team']
                print(colored("Created: " + data['email'], 'cyan'))


            except:
                print(colored(data['email'] + " already exists", 'red'))
                user = all_users_from_db[data['email']]
                localId = user['id']
                new_users_data['users/'+localId+'/firstName'] = data['firstName']
                new_users_data['users/'+localId+'/lastName'] = data['lastName']
                new_users_data['users/'+localId+'/summoner'] = data['summoner']
                new_users_data['users/'+localId+'/username'] = data['summoner']
                new_users_data['users/'+localId+'/team'] = data['team']
                new_users_data['users/'+localId+'/event'] = data['event']
                #add to teams
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/firstName"] = data['firstName']
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/lastName"] = data['lastName']
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/summoner"] = data['summoner']
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/username"] = data['summoner']
                new_users_data['liveEvents/'+event+'/teams/'+data['team']+"/"+localId+"/status"] = 'offline'
                # #add to event users list
                new_users_data['liveEvents/'+event+'/users/'+localId+"/firstName"] = data['firstName']
                new_users_data['liveEvents/'+event+'/users/'+localId+"/lastName"] = data['lastName']
                new_users_data['liveEvents/'+event+'/users/'+localId+"/summoner"] = data['summoner']
                new_users_data['liveEvents/'+event+'/users/'+localId+"/username"] = data['summoner']
                new_users_data['liveEvents/'+event+'/users/'+localId+"/team"] = data['team']

            #update event data
            #teams and users

        try:
            self.db.update(new_users_data)
            print(colored("Database Updated Succesfully", "green"))
            print(colored("Logos, Database data, and colors needed for:", "cyan"))
            print(new_teams)
        except:
            print(colored("Failed to update database", 'red'))

    def createMatchResultImages(self, event):
        match_dates = []
        matches_list = []
        current_matches = []
        matches_unsorted = []
        matches_sorted = []
        teamRecords = {}
        #get matches from databae
        matches_db = self.db.child("liveEvents/"+event+"/matches").get()
        for data in matches_db.each():
            if('winner' in data.val()):
                matches_unsorted.append({
                        'blueTeam' : data.val()['blueTeam'],
                        'redTeam' : data.val()['redTeam'],
                        'date' : data.val()['date'],
                        'redScore': data.val()['redScore'],
                        'blueScore': data.val()['blueScore'],
                        'winner': data.val()['winner'],
                })
        matches_sorted = sorted(matches_unsorted, key=lambda k: k['date']) 
        for data in matches_sorted:
            if data['date'] not in match_dates:
                match_dates.append(data['date'])
                if(len(current_matches) > 0):
                    matches_list.append(current_matches)
                    current_matches = []
            current_matches.append({
                'blueTeam' : data['blueTeam'],
                'redTeam' : data['redTeam'],
                'date' : data['date'],
                'redScore': data['redScore'],
                'blueScore': data['blueScore'],
                'winner': data['winner'],
            })
        team_db = self.db.child('liveEvents/'+event+'/teams').get()
        for team in team_db.each():
            teamRecords[team.key()] = {}
            teamRecords[team.key()]['wins'] = team.val()['wins']
            teamRecords[team.key()]['losses'] = team.val()['losses']
        teamsData = self.db.child("teamData").get()
        teamData = {}
        for data in teamsData.each():
            teamData[data.key()] = data.val()
        matches_list.append(current_matches)
        print(match_dates)
        date_select = int(input("Select index of date to generate: "))
        
        daytime = match_dates[date_select].split("T")[0].split("-")
        month = datetime(int(daytime[0]), int(daytime[1]), int(daytime[2])).strftime("%B")
        day = datetime(int(daytime[0]), int(daytime[1]), int(daytime[2])).strftime("%d")
        time = match_dates[date_select].split("T")[1]
        date = month + " " + day 
        matches = matches_list[date_select]
        makedirs("GenImages/"+event+"/matchResults/"+date, exist_ok=True)
        for match in matches_list[date_select]:
            blueTeam = match['blueTeam']
            redTeam = match['redTeam']
            winner = match['winner']
            blueWins = teamRecords[blueTeam]['wins']
            blueLosses = teamRecords[blueTeam]['losses']
            redWins = teamRecords[redTeam]['wins']
            redLosses = teamRecords[redTeam]['losses']
            blueRecord = "(" + str(blueWins) +"-" + str(blueLosses) + ")"
            redRecord = "(" + str(redWins) +"-" + str(redLosses) + ")"
            blueScore = match['blueScore']
            redScore = match['redScore']
            left_shadow = Image.open("./images/shadows/"+teamData[blueTeam.split("-")[0]]['light']+"-shadow.png")
            right_shadow = Image.open("./images/shadows/"+teamData[redTeam.split("-")[0]]['light']+"-shadow.png")
            left_team_img = Image.open("./images/teams/"+blueTeam+".png")
            right_team_img = Image.open("./images/teams/"+redTeam+".png")
            
            new_img = Image.new('RGB', (1080, 1080), color=(255, 255, 255))
            right_mask = Image.new("L", (1080, 1080), color=255)
            right_mask_draw = ImageDraw.Draw(right_mask)
            transparent_area = (0,0,540, 1080)
            right_mask_draw.rectangle(transparent_area, fill=0)
            right_shadow.putalpha(right_mask)
            if blueTeam.split("-")[0] == redTeam.split("-")[0]:
                right_shadow_enhancer = ImageEnhance.Brightness(right_shadow)
                right_shadow = right_shadow_enhancer.enhance(0.84)
            new_img.paste(left_shadow, (0,0))
            new_img.paste(right_shadow, (0,0), right_shadow)
            right_team_img = right_team_img.resize((600, 600), Image.ANTIALIAS)
            left_team_img = left_team_img.resize((600, 600), Image.ANTIALIAS)
            new_img.paste(right_team_img, (638, 390), right_team_img)
            new_img.paste(left_team_img, (-147, 390), right_team_img)
            date_frame = Image.new("RGB", (1080, 174), color=(255, 255, 255) )
            date_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 77)
            date_draw = ImageDraw.Draw(date_frame)
            date_width = date_draw.textsize(date, font=date_font)[0]
            date_height = date_draw.textsize(date, font=date_font)[1]
            date_2020logo = Image.open("./images/2020logo.png")
            date_2020logo.thumbnail((100, 100))
            date_padding = 30
            date_draw.text(((1080-date_width)//2+(100+date_padding)//2, (174-date_height)//2-25), date, (0,0,0), font=date_font)
            date_frame.paste(date_2020logo, ((1080-date_width-100)//2,(174-date_height)//2+14), date_2020logo)
            new_img.paste(date_frame, (0, 1080-174))
            score_frame = Image.new("RGB", (2*174, 174), color=(255, 255, 255))
            score_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 105)
            score_dash_draw = ImageDraw.Draw(score_frame)
            score_dash_width = score_dash_draw.textsize("-", font=score_font)[0]
            score_dash_draw.text(((2*174-score_dash_width)//2, -20), "-", (0,0,0), font=score_font)
            score_red_draw = ImageDraw.Draw(score_frame)
            score_red_width = score_red_draw.textsize(str(redScore), font=score_font)[0]
            score_red_draw.text((174+(174-score_red_width)//2, -15), str(redScore), (0,0,0) if winner == redTeam else (150, 150, 150), font=score_font)
            score_blue_draw = ImageDraw.Draw(score_frame)
            score_blue_width = score_blue_draw.textsize(str(blueScore), font=score_font)[0]
            score_blue_draw.text(( (174-score_blue_width)//2, -15), str(blueScore), (0,0,0) if winner == blueTeam else (150, 150, 150), font=score_font)
            new_img.paste(score_frame, ((1080-2*173)//2, 200))
            team_name_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 42)
            score_blue_team_draw = ImageDraw.Draw(new_img)
            score_blue_team_width = score_blue_team_draw.textsize(blueTeam, font=team_name_font)[0]
            score_blue_team_draw.text((50, 55), blueTeam, (255, 255, 255), font=team_name_font)
            record_font = ImageFont.truetype("./fonts/Cairo-Regular.ttf", 42)
            score_blue_record_draw = ImageDraw.Draw(new_img)
            score_blue_team_draw.text((50, 102), blueRecord, (255, 255, 255), font=record_font)
            score_red_team_draw = ImageDraw.Draw(new_img)
            score_red_width = score_red_team_draw.textsize(redTeam, font=team_name_font)[0]
            score_red_team_draw.text((1080-score_red_width-50, 55), redTeam, (255, 255, 255), font=team_name_font)
            score_red_record_draw = ImageDraw.Draw(new_img)
            score_red_record_width = score_red_record_draw.textsize(redRecord, font=record_font)[0]
            score_red_team_draw.text((1080-50-score_red_record_width, 102), redRecord, (255, 255, 255), font=record_font)
            # new_img.paste()
            new_img.save("GenImages/"+event+"/matchResults/"+date+"/"+blueTeam+"vs"+redTeam+".png")
        print(colored('Match Result Images Genereated', 'green'))
            
    def createStatImages(self, event):
        stat_weeks = []
        stats_data = []
        kills_unsorted = []
        assists_unsorted = []
        deaths_unsorted = []
        damage_unsorted = []
        gold_unsorted = []
        visionScore_unsorted = []
        chosen_week = 0

        stats = self.db.child("liveEvents/"+event+"/statsByWeek/").get()
        for week in stats.each():
            stat_weeks.append(week.key())
        
        print(stat_weeks)
        chosen_week = int(input(colored("Select index of week to generate:", 'magenta')))
        week_n = input(colored("Enter week number for event: ", 'magenta'))
        week = "WEEK "+  week_n 
        makedirs("GenImages/"+event+"/stats/"+week_n, exist_ok=True)
        kills = self.db.child("liveEvents/"+event+"/statsByWeek/"+stat_weeks[chosen_week]+"/kills").get()
        for user in kills.each():
            kills_unsorted.append({
                'username': user.val()['username'],
                'team': user.val()['team'],
                'name': user.val()['name'],
                'kills': user.val()['kills'],
                'champion': user.val()['champion']
            })
        kills_sorted = sorted(kills_unsorted, reverse=True, key=lambda k: k['kills'])

        assists = self.db.child("liveEvents/"+event+"/statsByWeek/"+stat_weeks[chosen_week]+"/assists").get()
        for user in assists.each():
            assists_unsorted.append({
                'username': user.val()['username'],
                'team': user.val()['team'],
                'name': user.val()['name'],
                'assists': user.val()['assists'],
                'champion': user.val()['champion']
            })
        assists_sorted = sorted(assists_unsorted, reverse=True, key=lambda k: k['assists'])

        deaths = self.db.child("liveEvents/"+event+"/statsByWeek/"+stat_weeks[chosen_week]+"/deaths").get()
        for user in deaths.each():
            deaths_unsorted.append({
                'username': user.val()['username'],
                'team': user.val()['team'],
                'name': user.val()['name'],
                'deaths': user.val()['deaths'],
                'champion': user.val()['champion']
            })
        deaths_sorted = sorted(deaths_unsorted,  key=lambda k: k['deaths'])

        gold = self.db.child("liveEvents/"+event+"/statsByWeek/"+stat_weeks[chosen_week]+"/gold").get()
        for user in gold.each():
            gold_unsorted.append({
                'username': user.val()['username'],
                'team': user.val()['team'],
                'name': user.val()['name'],
                'gold': round(user.val()['gold'], 1),
                'champion': user.val()['champion']
            })
        gold_sorted = sorted(gold_unsorted, reverse=True, key=lambda k: k['gold'])

        damage = self.db.child("liveEvents/"+event+"/statsByWeek/"+stat_weeks[chosen_week]+"/damage").get()
        for user in damage.each():
            damage_unsorted.append({
                'username': user.val()['username'],
                'team': user.val()['team'],
                'name': user.val()['name'],
                'damage': round(user.val()['damage'], 1),
                'champion': user.val()['champion']
            })
        damage_sorted = sorted(damage_unsorted, reverse=True, key=lambda k: k['damage'])

        visionScore = self.db.child("liveEvents/"+event+"/statsByWeek/"+stat_weeks[chosen_week]+"/visionScore").get()
        for user in visionScore.each():
            visionScore_unsorted.append({
                'username': user.val()['username'],
                'team': user.val()['team'],
                'name': user.val()['name'],
                'visionScore': user.val()['visionScore'],
                'champion': user.val()['champion']
            })
        visionScore_sorted = sorted(visionScore_unsorted, reverse=True, key=lambda k: k['visionScore'])
        teamsData = self.db.child("teamData").get()
        teamData = {}
        for data in teamsData.each():
            teamData[data.key()] = data.val()

        images = ['ELIMINATIONS', 'ASSISTS', 'DEATHS', 'GOLD', "VISION SCORE", 'DAMAGE']
        image_data = [kills_sorted, assists_sorted, deaths_sorted, gold_sorted, visionScore_sorted, damage_sorted]
        image_properties = ['kills', 'assists', 'deaths', 'gold', 'visionScore', 'damage']

        for i in range(0,len(images)):
            title = images[i]
            background_champ = image_data[i][0]['champion']
            background_color = teamData[image_data[i][0]['team'].split("-")[0]]['light']+'-shadow.png'
            f = open('./images/champ_splashes/'+background_champ+'.jpg','wb')
            f.write(request.urlopen('https://ddragon.leagueoflegends.com/cdn/img/champion/splash/'+background_champ+'_0.jpg').read())
            f.close()
            new_img = Image.new("RGB", (1080, 1080), color=(0, 255, 255))
            background_champ_img =Image.open('./images/champ_splashes/'+background_champ+'.jpg')
            new_champ_width = int(background_champ_img.size[0]*1.6)
            new_champ_height = int(background_champ_img.size[1]*1.6)
            background_champ_img = background_champ_img.resize((new_champ_width,new_champ_height), Image.ANTIALIAS)
            background_champ_enhancer = ImageEnhance.Color(background_champ_img)
            background_champ_img = background_champ_enhancer.enhance(0)
            background_champ_enhancer = ImageEnhance.Contrast(background_champ_img)
            background_champ_img = background_champ_enhancer.enhance(1.5)
            background_champ_mask = Image.new("RGB", (1080, 1080), color = (0,0,0))
            background_champ_mask.paste(background_champ_img, (-600, 0))
            shadow = Image.open("./images/shadows/"+background_color)
            shadow = shadow.crop((200, 200, 880, 880))
            shadow = shadow.resize((1080,1080), Image.ANTIALIAS)
            background = Image.blend(shadow, background_champ_mask, 0.3)
            new_img.paste(background, (0, 0))
            title_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 100)
            title_draw = ImageDraw.Draw(new_img)
            title_width = title_draw.textsize(title, font=title_font)[0]
            title_draw.text(( (1080-title_width)//2, 0), title, color=(255, 255, 255), font=title_font)
            subtitle_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 60)
            subtitle_draw = ImageDraw.Draw(new_img)
            subtitle_width = subtitle_draw.textsize(week, font=subtitle_font)[0]
            subtitle_draw.text(( (1080-subtitle_width)//2, 130), week, color=(255, 255, 255), font=subtitle_font)
            
            row_width = 1080-2*74
            row_spacing = 15
            for x in range(0,5):
                name = image_data[i][x]['name'] +" ( "+image_data[i][x]['username'] +" )"
                background_champ = image_data[i][x]['champion']
                team = image_data[i][x]['team']
                stat = image_data[i][x][image_properties[i]]
                row_frame = Image.new("RGB", (row_width, 110), color=(255, 255, 255))
                f = open('./images/champ_icons/'+background_champ+'.png','wb')
                f.write(request.urlopen('http://ddragon.leagueoflegends.com/cdn/9.24.2/img/champion/'+background_champ+'.png').read())
                f.close()
                champ_icon = Image.open("./images/champ_icons/"+background_champ+'.png')
                champ_icon.thumbnail((110, 110), Image.ANTIALIAS)
                row_frame.paste(champ_icon, (0,0))
                team_icon = Image.open("./images/teams/"+team+".png")
                team_icon.thumbnail((35,35), Image.ANTIALIAS)
                row_frame.paste(team_icon, (75,75), team_icon)
                placement_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 75)
                placement_text_draw = ImageDraw.Draw(row_frame)
                placement_text_draw.text((125, -20), str(x+1)+".", (10,10,10), font=placement_font)
                name_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 28)
                name_text_draw = ImageDraw.Draw(row_frame)
                name_text_draw.text((200, 10), name, (10,10,10), font=name_font)
                teamname_text_draw = ImageDraw.Draw(row_frame)
                hexa = teamData[team.split("-")[0]]['light'].strip("#")
                hexa_to_rgb =  tuple(int(hexa[i:i+2], 16) for i in (0, 2, 4))
                teamname_text_draw.text((200, 42), team, hexa_to_rgb, font=name_font)
                five_text_draw = ImageDraw.Draw(row_frame)
                five_text_draw.text((row_width-110, 42), "/5mins", hexa_to_rgb, font=name_font)
                stat_text_draw = ImageDraw.Draw(row_frame)
                stat_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 75 if image_properties[i] != 'damage' else 55)
                stat_text_width = stat_text_draw.textsize(str(stat), font=stat_font)[0]
                stat_text_draw.text((row_width-110-stat_text_width-5, -18  if image_properties[i] != 'damage' else 8), str(stat), (0,0,0), font=stat_font)
                new_img.paste(row_frame, (74, 260+110*x +row_spacing*x))
            trans_logo = Image.open("./images/2020logo-transparent.png")
            trans_logo.thumbnail((207, 107), Image.ANTIALIAS)
            new_img.paste(trans_logo, ((1080 - trans_logo.size[0])//2, 1080-160), trans_logo)
            new_img.save("GenImages/"+event+"/stats/"+week_n+"/"+image_properties[i]+week_n+".png")
        print(colored("Stat Images Succesfully generated", "green"))
        

            

            



    def createScheduleImages(self, event):
        render_width = 1080
        render_height = 1080
        match_dates = []
        matches_list = []
        current_matches = []
        matches_unsorted = []
        matches_sorted = []
        #get matches from databae
        matches_db = self.db.child("liveEvents/"+event+"/matches").get()
        for data in matches_db.each():
            matches_unsorted.append({
                    'blueTeam' : data.val()['blueTeam'],
                    'redTeam' : data.val()['redTeam'],
                    'date' : data.val()['date']
                })
        matches_sorted = sorted(matches_unsorted, key=lambda k: k['date']) 
        for data in matches_sorted:
            if data['date'] not in match_dates:
                match_dates.append(data['date'])
                if(len(current_matches) > 0):
                    matches_list.append(current_matches)
                    current_matches = []
            current_matches.append({
                'blueTeam' : data['blueTeam'],
                'redTeam' : data['redTeam'],
            })
        matches_list.append(current_matches)
        makedirs("GenImages/"+event+"/schedule", exist_ok=True)
        for i in range(0, len(match_dates)):
            daytime = match_dates[i].split("T")[0].split("-")
            month = datetime(int(daytime[0]), int(daytime[1]), int(daytime[2])).strftime("%B")
            day = datetime(int(daytime[0]), int(daytime[1]), int(daytime[2])).strftime("%d")
            date = month + " " + day
            time = match_dates[i].split("T")[1]
            matches = matches_list[i]
            for match in range(0, len(matches) // 4 + 1):
                if(match*4 == len(matches)): break
                #initiate background shadow as canvas
                new_img = Image.new('RGB', (render_width, render_height), color=(255, 255, 255))
                shadow = Image.open("./images/shadow.png")
                shadow.thumbnail((1080, 1080), Image.ANTIALIAS)
                new_img.paste(shadow, (0,0))
                #title
                the_void = Image.new("RGBA", (1080, 200) , (255, 255, 255, 0))
                title_frame_wrapper_height = 0 
                title_frame_wrapper_width = 0 
                title_frame = Image.new("RGBA", (render_width, 230), color=(255, 255, 255, 0))
                title_frame_2020logo = Image.open('./images/2020logo.png')
                title_frame_2020logo.thumbnail((213, 146), Image.ANTIALIAS)
                title_frame_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 77)
                title_frame_date_draw = ImageDraw.Draw(the_void)
                title_frame_font_padding = 18
                title_frame_font_width = title_frame_date_draw.textsize(date, font=title_frame_font)[0]
                title_frame_date_frame = Image.new("RGBA", (title_frame_font_width, 90), color=(0, 0, 0, 1))
                title_frame_time_frame = Image.new("RGBA", (title_frame_font_width, 146//2), color=(0, 0, 0, 1))
                title_frame_date_draw = ImageDraw.Draw(title_frame_date_frame)
                title_frame_date_draw.fontmode = '1'
                title_frame_time_draw = ImageDraw.Draw(title_frame_time_frame)
                title_frame_time_draw.fontmode = '1'
                title_frame_wrapper = Image.new("RGBA", (213 + title_frame_font_padding + title_frame_font_width, 146), color=(255, 255, 255, 0))
                title_frame_wrapper.paste(title_frame_2020logo, (0,0), title_frame_2020logo)
                title_frame_date_draw.text((0,-37), date, (0,0,0), font=title_frame_font)
                title_frame_time_draw.text((0,-42), time, (0,0,0), font=title_frame_font)
                title_frame_wrapper.paste(title_frame_date_frame, (213 + title_frame_font_padding,0), title_frame_date_frame)
                title_frame_wrapper.paste(title_frame_time_frame, (213 + title_frame_font_padding,146//2), title_frame_time_frame)
                title_frame_wrapper.thumbnail((213+title_frame_font_width, 146), Image.ANTIALIAS)
                title_frame_wrapper_width = int( (1080-213-title_frame_font_width)/2 )
                title_frame_wrapper_height = int ( (230-146)/2 )
                title_frame.paste(title_frame_wrapper, (title_frame_wrapper_width ,title_frame_wrapper_height), title_frame_wrapper)
                new_img.paste(title_frame, (0,0), title_frame)

                #one row of the matchup
                matchF_spacing = 32
                for x in range(0,4):
                    if(len(matches) == match*4+x): break
                    match_f_width = 1080-2*74
                    matchF = Image.new("RGB", (match_f_width, 130), color=(255, 255, 255))
                    matchF_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 30)
                    matchF_vs_frame = Image.new("RGBA", (60, 130), color=(210, 210, 210, 0))
                    matchF_vs_draw = ImageDraw.Draw(matchF_vs_frame)
                    matchF_vs_height = matchF_vs_draw.textsize("VS", font=matchF_font)[1]
                    matchF_vs_width = matchF_vs_draw.textsize("VS", font=matchF_font)[0]
                    matchF_vs_height_centerPos = (115-matchF_vs_height) // 2
                    matchF_vs_width_centerPos = (60-matchF_vs_width) // 2
                    matchF_vs_draw.text((matchF_vs_width_centerPos, matchF_vs_height_centerPos), "VS", (210,210,210), font=matchF_font)
                    matchF.paste(matchF_vs_frame, ((match_f_width-60)//2,0), matchF_vs_frame)
                    matchF_Lteam_frame = Image.new("RGBA", (93, 93), color=(255, 0, 0, 0))
                    matchF_Lteam_image = Image.open("./images/teams/"+matches[match*4+x]['blueTeam']+'.png')
                    matchF_Lteam_image.thumbnail((93, 93), Image.ANTIALIAS)
                    matchF_Lteam_frame.paste(matchF_Lteam_image, (0, 0), matchF_Lteam_image)
                    matchF.paste(matchF_Lteam_frame, ((match_f_width-60-2*93)//2, (130-93)//2 ), matchF_Lteam_frame)
                    matchF_Rteam_frame = Image.new("RGBA", (93, 93), color=(255, 0, 0, 0))
                    matchF_Rteam_image = Image.open("./images/teams/"+matches[match*4+x]['redTeam']+'.png')
                    matchF_Rteam_image.thumbnail((93, 93), Image.ANTIALIAS)
                    matchF_Rteam_frame.paste(matchF_Rteam_image, (0, 0), matchF_Rteam_image)
                    matchF.paste(matchF_Rteam_frame, ((match_f_width-60-2*93)//2 + 60 + 93, (130-93)//2 ), matchF_Rteam_frame)
                    matchF_Rteam_draw = ImageDraw.Draw(matchF)
                    matchF_Rteam_draw.text((match_f_width - 321 ,matchF_vs_height_centerPos), matches[match*4+x]['redTeam'], (0,0,0), font=matchF_font)
                    matchF_Lteam_draw = ImageDraw.Draw(matchF)
                    matchF_Lteam_textSize = matchF_Lteam_draw.textsize(matches[match*4+x]["blueTeam"], font=matchF_font)[0]
                    matchF_Rteam_draw.text( (321 - matchF_Lteam_textSize ,matchF_vs_height_centerPos) , matches[match*4+x]['blueTeam'], (0,0,0), font=matchF_font)
                    new_img.paste(matchF, (74, 230+130*x +matchF_spacing*x))
            
            new_img.save("GenImages/"+event+"/schedule/"+month+day+time.split(":")[0]+".png")
        print(colored('Schedule images for event:'+event+' succesfully created in python/GenImages/Schedule', 'green'))

    def createRosterImages(self, event):
        render_width = 1080
        render_height = 1080
        teams = []
        teamData = {}
        #get team color data
        teamsData = self.db.child("teamData").get()
        for data in teamsData.each():
            teamData[data.key()] = data.val()
        #get matches from databae
        teams_db = self.db.child("liveEvents/"+event+"/teams").get()
        for data in teams_db.each():
            team = []
            for member in data.val().keys():
                if 'firstName' in data.val()[member]: 
                    team.append({
                        'name': data.val()[member]['firstName'] + data.val()[member]['lastName'],
                        'team': data.key(),
                        'handle': data.val()[member]['summoner'],
                        'shadow': teamData[data.key().split("-")[0]]['light']+'-shadow'
                    })
            teams.append(team)
        makedirs("GenImages/"+event+"/AcademyRosterReveal", exist_ok=True)
        for team in teams:
            #initiate background shadow as canvas
            new_img = Image.new('RGB', (render_width, render_height), color=(255, 255, 255))
            shadow = Image.open("./images/shadows/"+team[0]["shadow"]+".png")
            shadow.thumbnail((1080, 1080), Image.ANTIALIAS)
            new_img.paste(shadow, (0,0))
            #title
            the_void = Image.new("RGBA", (1080, 200) , (255, 255, 255, 0))
            title_frame_wrapper_height = 0 
            title_frame_wrapper_width = 0 
            title_frame = Image.new("RGBA", (render_width, 230), color=(255, 255, 255, 0))
            title_frame_2020logo = Image.open('./images/teams/'+team[0]['team']+'.png')
            title_frame_2020logo.thumbnail((110, 110))
            title_frame_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 65)      
            title_frame_date_draw = ImageDraw.Draw(the_void)
            title_frame_font_width = title_frame_date_draw.textsize(team[0]['team'], font=title_frame_font)[0]


            title_frame_wrapper = Image.new("RGBA", (213 + title_frame_font_width, 146), color=(255, 255, 255, 0))
            team_name_draw = ImageDraw.Draw(title_frame_wrapper)
            team_name_draw.text((120, 0),team[0]['team'], (255, 255, 255),  font=title_frame_font)
            title_frame_wrapper.paste(title_frame_2020logo, (0,10), title_frame_2020logo)
            title_frame_wrapper.thumbnail((213+title_frame_font_width, 146), Image.ANTIALIAS)
            title_frame_wrapper_width = int( (1080-130-title_frame_font_width)/2 )
            title_frame_wrapper_height = int ( (230-146)/2 )
            title_frame.paste(title_frame_wrapper, (title_frame_wrapper_width ,title_frame_wrapper_height), title_frame_wrapper)
            new_img.paste(title_frame, (0,0), title_frame)
            
            #one row of the matchup
            matchF_spacing = 32
            match_f_width = 1080-2*74
            matchF = Image.new("RGBA", (match_f_width, 90), color=(255, 255, 255, 0))
            matchF_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 40)
            matchF_name_frame = Image.new("RGBA", (60, 90), color=(210, 210, 210, 0))
            matchF_name_draw = ImageDraw.Draw(matchF_name_frame)
            matchF_name_height = matchF_name_draw.textsize('Name', font=matchF_font)[1]
            matchF_name_height_centerPos = (75-matchF_name_height) // 2
            matchF_name_draw = ImageDraw.Draw(matchF)
            matchF_name_draw.text((50, matchF_name_height_centerPos), 'Name', (255,255,255), font=matchF_font)
            matchF_Rteam_draw = ImageDraw.Draw(matchF)
            matchF_Rteam_draw.text((400,matchF_name_height_centerPos), 'Handle', (255,255,255), font=matchF_font)
            new_img.paste(matchF, (74, 160), matchF)
            x = 1
            for member in team:
                match_f_width = 1080-2*74
                color = 0;
                if x%2== 0: color = 13
                matchF = Image.new("RGB", (match_f_width, 90), color=(255-color, 255-color, 255-color))
                matchF_font = ImageFont.truetype("./fonts/Cairo-Regular.ttf", 30)
                matchF_name_frame = Image.new("RGBA", (60, 90), color=(210, 210, 210, 0))
                matchF_name_draw = ImageDraw.Draw(matchF_name_frame)
                matchF_name_height = matchF_name_draw.textsize(member['name'], font=matchF_font)[1]
                matchF_name_height_centerPos = (75-matchF_name_height) // 2
                matchF_name_draw = ImageDraw.Draw(matchF)
                matchF_name_draw.text((50, matchF_name_height_centerPos), member['name'], (0,0,0), font=matchF_font)
                matchF_Rteam_draw = ImageDraw.Draw(matchF)
                matchF_Rteam_draw.text((400,matchF_name_height_centerPos), member['handle'], (0,0,0), font=matchF_font)
                new_img.paste(matchF, (74, 160+90*x))
                x+=1
        
            new_img.save("GenImages/"+event+"/AcademyRosterReveal/"+team[0]['team']+".png")
        print(colored('RosterReveal for event:'+event+' images succesfully', 'green'))

    def createMog(self):
        mog_path = "./mog/submissions"
        orgs = ['1. frostbite', '2. frostbite_academy', '3. wizards', '4. wizards_academy', '5. warhawks', '6. warhawks_academy', '7. tempo', '8. tempo_academy',
                '9. mischief', '10. mischief_academy', '11. hydra', '12. hydra_academy', "13. eclipse", '14. eclipse_academy', '15. honor', '16. honor_academy']
        org_colors = ['cyan', 'cyan', 'pink_1', 'pink_1', 'red', 'red', 'blue', 'blue', 'green', 'green', 'purple_1b', 'purple_1b', 'dark_orange_3a', 'dark_orange_3a', 'yellow', 'yellow']
        files = [f for f in listdir(mog_path) if isfile(join(mog_path, f))]
        files_show = len(files) * [None]
        for x in range(len(files)):
            files_show[x] = str(x+1) + ". "+files[x]
        print(files_show[x] )
        submission = input(colored('Select a file:', 'yellow'))
        file = files[int(submission) - 1]    
        for x in range(len(orgs)):
            print(stylize(orgs[x], fg(org_colors[x])) )
        team_n = int(input(colored("Choose a team: ", 'yellow'))) - 1
        team = orgs[team_n].split(". ")[1]
        org = team.split("_")[0]
        team_name = input(colored("Enter team (school with number): ", "yellow"))
        name = input(colored("Full name: ", "yellow"))
        clipStart = int(input(colored("Enter clip start(seconds): ", "yellow")))
        clipEnd = int(input(colored("Enter clip end(seconds): ", "yellow")))
        name_baner = team_name + ": " + name
        date = str(datetime.now().strftime("%y%m%d"))
        file_name = date+team_name        
        #create name overlay
        template = Image.new("RGBA", (1920, 1080), (0,0,0,0))
        team_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 70)
        team_draw = ImageDraw.Draw(template)
        team_draw.text((345, 775),team_name, (7, 7, 7), font=team_font)
        team_font = ImageFont.truetype("./fonts/Cairo-Regular.ttf", 60)
        team_draw = ImageDraw.Draw(template)
        team_draw.text((345, 870),name, (7, 7, 7), font=team_font)
        template.save("./mog/gen_name/"+"name.png")
        clip = VideoFileClip("./mog/submissions/"+file)
        clip.resize((1920,1080))
        end = VideoFileClip("./mog/end.mp4")
        team_overlay = VideoFileClip("./mog/team_overlays/"+team+".avi", has_mask=True)
        teamData = {}
        teamsData = self.db.child("teamData").get()
        for data in teamsData.each():
            teamData[data.key()] = data.val()
        #create thumbnail
        tn = Image.new("RGB", (1920,1080), (0,0,0))
        clip.save_frame('./mog/gen_thumbnails/'+file_name+".png", t=10)
        tn_from_video = Image.open('./mog/gen_thumbnails/'+file_name+".png")
        tn_team_overlay = Image.open('./mog/thumbnail_overlays/'+org+"_tn_overlay.png")
        video_enhancer = ImageEnhance.Color(tn_from_video)
        tn_from_video = video_enhancer.enhance(0)
        video_enhancer = ImageEnhance.Contrast(tn_from_video)
        tn_from_video = video_enhancer.enhance(2)
        video_enhancer = ImageEnhance.Brightness(tn_from_video)
        tn_from_video = video_enhancer.enhance(0.9)
        tn_from_video = tn_from_video.crop((100*16/9,100, 1920-100*16/9, 1080-100))
        tn_from_video = tn_from_video.resize((int(1920), int(1080)), Image.ANTIALIAS)
        hexa = teamData[team_name.split("-")[0]]['dark'].strip("#")
        hexa_to_rgb =  tuple(int(hexa[i:i+2], 16) for i in (0, 2, 4))
        color_overlay = Image.new("RGB", (1920,1080), hexa_to_rgb) 
        background_blend = Image.blend(tn_from_video, color_overlay, alpha=0.4)
        tn.paste(background_blend, (0,0))
        tn.paste(tn_team_overlay, (0,0), tn_team_overlay)
        team_img = Image.open("./images/teams/"+team_name+".png")
        team_img = team_img.resize((400, 400), Image.ANTIALIAS)
        tn.paste(team_img, (270, 640), team_img)
        hexa = teamData[team_name.split("-")[0]]['dark'].strip("#")
        hexa_to_rgb =  tuple(int(hexa[i:i+2], 16) for i in (0, 2, 4))
        name_overlay = Image.new("RGB", (1920, 100), hexa_to_rgb)
        event_logo = Image.open("./images/2020logo-transparent.png")
        event_logo.thumbnail((90, 90), Image.ANTIALIAS)
        name_overlay.paste(event_logo, (405, 20), event_logo)
        name_draw = ImageDraw.Draw(name_overlay)
        name_font = ImageFont.truetype("./fonts/Cairo-Bold.ttf", 50)
        name_width = name_draw.textsize(name_baner , font=name_font)[0]
        name_draw.text(((1920-name_width)//2,0), name_baner, (255, 255, 255), font=name_font)
        tn.paste(name_overlay, (0, 1080-100))
        tn.save("./mog/gen_thumbnails/"+name+date+".png")
        thumbnail_video = ImageClip("./mog/gen_thumbnails/"+name+date+".png").set_duration(0.001)
        name_overlay = ImageClip("./mog/gen_name/name.png").set_duration(3.1)
        final = CompositeVideoClip([clip.subclip(clipStart,clipEnd), thumbnail_video, team_overlay.set_start(0.5), name_overlay.set_start(0.33+0.5).crossfadein(0.1), end.set_start(clipEnd-clipStart - 0.4).crossfadein(0.4)])
        final.write_videofile("./mog/finished/"+name+date+".mp4")
olae = Olae()
# olae.addUsersFromSpreadsheet('olae2222', 'olae2020')
# olae.genRegularSeasonMatches('olae2222', 5, 2020, 2, 14, '20:00')
olae.createScheduleImages('olae2020-preseason')
# olae.createRosterImages('olae2020-preseason')
# olae.createMatchResultImages('olae2020-preseason')
# olae.createStatImages('olae2222')
# olae.createMog()
