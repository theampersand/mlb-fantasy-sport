import myql
import json
import csv
import datetime
from myql.contrib.auth import YOAuth

#Trying to write data to CSV
csv.register_dialect('ALM', delimiter=',', quoting=csv.QUOTE_ALL)
    
    
def make_league_code(gameid, leagueid):
    return str(gameid) + '.l.' + str(leagueid)

def make_team_code(gameid, leagueid, teamid):
    return str(gameid) + '.l.' + str(leagueid) + '.t.' + str(teamid)

def league_data(league_code):
    return "http://fantasysports.yahooapis.com/fantasy/v2/league/" + league_code

def team_data(team_code):
    return "http://fantasysports.yahooapis.com/fantasy/v2/team/" + team_code

def roster_data(team_code, date_wanted):
    return "http://fantasysports.yahooapis.com/fantasy/v2/team/" + team_code + "/roster;date=" + date_wanted.isoformat()
        
league = []
teams = []
rosters = []

oauth = YOAuth(None, None, from_file='credentials.json')
y = myql.MYQL(format='json', oauth=oauth)
"""
# allows for multiple leagues
league_dict = [
        #2015
        {'gameid': 346, 'leagueid': 1328}
]

# Store league info
for l in league_dict:

  league_code = make_league_code(l['gameid'], l['leagueid'])
  league_info = y.yfs_league(league_code)
  #league_name = (league_info['league_name'])
  # Get number of teams
  num_teams = int(league_info['num_teams'])
  # add to list
  league.append(league_info)

#dates for organizing files  
next_date = league_info['edit_key']
next_date_form = datetime.datetime.strptime(next_date, "%Y-%m-%d")
curr_day_form = next_date_form + datetime.timedelta(days=-1) 


team_list = []
#Hardcoded league info for team info
gameid = 346
leagueid = 1328
    
#for i in range(1, (num_teams+1)):
#My team
for i in range(12, 13):

  teamid = i
  team_code = make_team_code(gameid, leagueid, teamid)
  team_list.append(team_code)
  
for t in team_list:

  team_info = y.yfs_team(t)
  #handle players
  roster_info = team_info['roster']['players']['player']
  
  #managers
  this_manager = team_info['managers']['manager']
  if type(this_manager) == list:
    this_manager = this_manager[0]
    
  if 'guid' in this_manager: manager_guid = this_manager['guid']
  if 'guid' not in this_manager: manager_guid = None
  team_info['manager_guid'] = manager_guid
  if 'email' in this_manager: manager_email = this_manager['email']
  if 'email' not in this_manager: manager_email = None
  team_info['manager_email'] = manager_email
  if "is_owned_by_current_login" not in team_info: team_info["is_owned_by_current_login"] = None
  
  team_info['manager_id'] = this_manager['manager_id']
  team_info['manager_nickname'] = this_manager['nickname']
  team_info['manager_email'] = this_manager['email']
  
  team_info.pop("managers", None)
  team_info.pop("team_logos", None)
  team_info.pop("roster_adds", None)
  team_info.pop("roster", None)
  
  print str(this_manager['nickname'])
  teams.append(team_info)
  
  #Set up roster info
  for k in roster_info:
    k['owner_email'] = manager_email
    k['owner_guid'] = manager_guid
    k['team_code'] = team_code
    k['date_captured'] = curr_day_form
    k['season'] = league_info['season']
    k['full_name'] = k['name']['full']
    k['first_name'] = k['name']['ascii_first']
    k['last_name'] = k['name']['ascii_last']
    k['image_url'] = k['headshot']['url']
    k['eligible_positions'] = k['eligible_positions']['position']
    k['selected_position'] = k['selected_position']['position']
    if "status" not in k: k["status"] = None
    if "starting_status" not in k: k["starting_status"] = None
    if "has_player_notes" not in k: k["has_player_notes"] = None
    if "has_recent_player_notes" not in k: k["has_recent_player_notes"] = None
    if "on_disabled_list" not in k: k["on_disabled_list"] = None
    if "is_editable" not in k: k["is_editable"] = None
    k.pop("headshot", None)
    k.pop("name", None)
    k.pop("editorial_player_key", None)
    k.pop("editorial_team_key", None)
    rosters.append(k)
"""  

#Use Put to make a roster change

# hardcode my team
team_code = '346.l.1328.t.12'

# David Peralta
hit1id = 9719
pos1 = 'OF'
# Jay Bruce
hit2id = 8171
pos2 = 'BN'

#If a player isn't starting or isn't as good, then make change

y.set_hitters(team_code)
print "Switch made"


#write data

y.data_to_csv(
  target_dir="data",
  data_to_write=league,
  desired_name='league'
  )


y.data_to_csv(
  target_dir="data",
  data_to_write=teams,
  desired_name='teams'
  )

y.data_to_csv(
  target_dir="data",
  data_to_write=rosters,
  desired_name='rosters'
  )
