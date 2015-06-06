import requests
from contrib.auth import YOAuth
import errors
import json
import importlib
#
import os
import os.path
import unicodecsv
#

__author__ = 'Josue Kouka'
__email__ = 'josuebrunel@gmail.com'

class MYQL(object):
  '''Yet another Python Yahoo! Query Language Wrapper
  Attributes:
  - url : data provider url
  - table : default table, so you won't have to specify a table later
  - format : default format of the responses
  - diagnostics : set to <True> to see diagnostics on queries
  - community : set to <True> to have access to community tables
  '''
  public_url = 'https://query.yahooapis.com/v1/public/yql'
  private_url = 'http://query.yahooapis.com/v1/yql'
  community_data  = "env 'store://datatables.org/alltableswithkeys'; " #Access to community table 
  
  def __init__(self, table=None, url=private_url, community=False, format='json', jsonCompact=True, crossProduct=None, debug=False, oauth=True):
    self.url = url
    self.table = table
    self.format = format
    self._query = None # used to build query when using methods such as <select>, <insert>, ...
    self._payload = {}
    self.diagnostics = False # Who knows, someone would like to turn it ON lol
    self.limit = ''
    self.community = community # True means access to community data
    self.format = format
    self.crossProduct = crossProduct
    self.jsonCompact = jsonCompact
    self.debug = debug
    
    if oauth:
        self.oauth = oauth

  def __repr__(self):
    '''Returns information on the current instance
    '''
    return "<url>: '{0}' - <table>: '{1}' -  <format> : '{2}' ".format(self.url, self.table, self.format)

  def payloadBuilder(self, query, format='json'):
    '''Build the payload'''
    if self.community :
      query = self.community_data + query # access to community data tables
      
    payload = {
	'q' : query,
	'callback' : '', #This is not javascript
	'diagnostics' : self.diagnostics, 
	'format' : format,
    'debug': self.debug,
    'jsonCompact': self.jsonCompact
    }
    if self.crossProduct:
        payload['crossProduct'] = self.crossProduct
    
    self._payload = payload
    
    return payload

  def rawQuery(self, query, format='json', pretty=True):
    '''Executes a YQL query and returns a response
       >>>...
       >>> resp = yql.rawQuery('select * from weather.forecast where woeid=2502265')
       >>> 
    '''
    if format:
      format = format
    else:
      format = self.format
    
    payload = self.payloadBuilder(query, format=format)
    response = self.executeQuery(payload)
    if pretty:
      response = self.buildResponse(response)

    return response

  def executeQuery(self, payload, pretty=False):
    '''Execute the query and returns and response'''
    if vars(self).get('oauth'): 
        self.url = self.private_url
        if not self.oauth.token_is_valid(): # Refresh token if token has expired
            self.oauth.refresh_token()
        response = self.oauth.session.get(self.url, params= payload)
    else:
        response = requests.get(self.url, params= payload)
        
    if pretty:
      response = self.buildResponse(response)

    return response
  """  
  def impQuery(self, payload):
    '''Execute the query and use put to implement the change'''
    self.url = self.private_url
    if not self.oauth.token_is_valid(): # Refresh token if has expired
      self.oauth.refresh_token()
    response = self.oauth.session.put(self.url, params= payload)
    else:
      # Not sure if will work but probably won't hit
      response = requests.put(self.url, params= payload)
      
    return response
  """
  def clauseFormatter(self, cond):
    '''Formats conditions
       args is a list of ['column', 'operator', 'value']
    '''
    if cond[1].lower() == 'in':
      cond[2] = "{0}".format(cond[2])
      cond = ' '.join(cond)
    else:
      cond[2] = "'{0}'".format(cond[2])
      cond = ''.join(cond)
      
    return cond
    
  def buildResponse(self, response):
    '''Try to return a pretty formatted response object
    '''
    try:
      r = response.json()
      result = r['query']['results']
      response = {
        'num_result': r['query']['count'] ,
        'result': result
      }
    except Exception, e:
      print(e)
      return response.content
    return response


  ######################################################
  #
  #                 MAIN METHODS
  #
  #####################################################

  ##USE
  def use(self, url):
    '''Changes the data provider
    >>> yql.use('http://myserver.com/mytables.xml')
    '''
    self.url = url
    return self.url

  ##DESC
  def desc(self, table=None):
    '''Returns table description
    >>> yql.desc('geo.countries')
    >>>
    '''
    if not table:
      #query = "desc {0} ".format(self.table)
      raise errors.NoTableSelectedError('No table selected')
    query = "desc {0}".format(table)
    response = self.rawQuery(query)

    return response

  ##GET
  def get(self, table=None, items=[], limit=''):
    '''Just a select which returns a response
    >>> yql.get("geo.countries', ['name', 'woeid'], 5")
    '''
    try:
      self.table = table
      if not items:
        items = ['*'] 
      self._query = "select {1} from {0} ".format(self.table, ','.join(items))
      if limit:
        self._query += "limit {0}".format(limit)

      if not self.table :
        raise errors.NoTableSelectedError('Please select a table')
       
      payload = self.payloadBuilder(self._query)
      response = self.executeQuery(payload)
    except Exception, e:
      print(e.text)

    return response
       
  ## SELECT
  def select(self, table=None, items=[], limit=''):
    '''This method simulate a select on a table
    >>> yql.select('geo.countries', limit=5) 
    >>> yql.select('social.profile', ['guid', 'givenName', 'gender'])
    '''
    try:
      self.table = table
      if not items:
        items = ['*']
      self._query = "select {1} from {0} ".format(self.table, ','.join(items))
      try: #Checking wether a limit is set or not
        self._limit = limit
      except Exception, e:
        pass
    except Exception, e:
      print(e)

    return self

  ## WHERE
  def where(self, *args):
    ''' This method simulates a where condition. Use as follow:
    >>>yql.select('mytable').where(['name', '=', 'alain'], ['location', '!=', 'paris'])
    '''
    if not self.table:
      raise errors.NoTableSelectedError('No Table Selected')

    clause = []
    self._query += ' where '
    for x in args:
      x = self.clauseFormatter(x)
      clause.append(x)

    self._query += ' and '.join(clause)

    if self._limit :
      self._query +=  " limit {0}".format(self._limit)

    payload = self.payloadBuilder(self._query)
    response = self.executeQuery(payload)

    return response
    
  ##PUT
  def put(self, address, date, hit1key, hit2key, pos1, pos2):
    ''' This method uses PUT to modify a resource
     encoding="UTF-8" ?'''
    xmlString = ('<?xml version="1.0"?>'
'<fantasy_content>'
  '<roster>'
    '<coverage_type>date</coverage_type>'
    '<date>%s</date>'

    '<players>'
      '<player>'
        '<player_key>%s</player_key>'
        '<position>%s</position>'
      '</player>'
      '<player>'
        '<player_key>%s</player_key>'
        '<position>%s</position>'
      '</player>'
    '</players>'
  '</roster>'
'</fantasy_content>') % (date, hit1key, pos1, hit2key, pos2)

    print xmlString[0:300]
    if vars(self).get('oauth'): 
      self.url = self.private_url
      if not self.oauth.token_is_valid(): # Refresh token if token has expired
        self.oauth.refresh_token()
            
    headers = {'content-Type':'application/xml'} # Specifying that we're working with xml        
    response = self.oauth.session.put(address, data=xmlString[0:300], headers=headers)
    
    if response.status_code == 200: # When request is successful
      return True
    else:
      print(response.reason) #print why it failed
    return False
    
    

  ######################################################
  #
  #                     HELPERS
  #
  #####################################################

  def getGUID(self, username):
    '''Returns the guid of the username provided
       >>> guid = self.getGUID('josue_brunel')
       >>> guid
    '''
    response = self.select('yahoo.identity').where(['yid', '=', username])
    
    return response
    
  def showTables(self, format='json'):
    '''Return list of all available tables'''

    query = 'SHOW TABLES'
    payload = self.payloadBuilder(query, format) 	

    response = self.executeQuery(payload) 

    return response

  ######################################################
  #
  #                     Fantasy Sports Package
  #
  ######################################################
  
  def yfs_league(self, league_code):
  
    #oauth = YOAuth(None, None, from_file='credentials.json')
    #yql = MYQL(format='json', oauth=oauth)
    response = self.select('fantasysports.leagues').where(['league_key','=',league_code])
    data = response.json()
    this_league = (data['query']['results']['league'])
    #league_name = (data['query']['results']['league']['league_name'])
    #num_teams = (data['query']['results']['league']['num_teams'])
    #return str(json.dumps({'League Name': league_name'Num of Teams': num_teams}))
    return this_league
      
  def yfs_team(self, team_code):
  
    response = self.select('fantasysports.teams.roster').where(['team_key','=',team_code])
    data = response.json()
    this_team = (data['query']['results']['team'])
    return this_team
    
  def data_to_csv(self, target_dir, data_to_write, desired_name):
    #Convenience function to write a dict to CSV with appropriate parameters.
    #generate directory if doesn't exist
    global d
    if len(data_to_write) == 0:
        return None
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    if type(data_to_write) == dict:
        #order dict by keys
        d = OrderedDict(sorted(data_to_write.items()))
        keys = d.keys()
    if type(data_to_write) == list:
        d = data_to_write
        keys = data_to_write[0].keys()
    with open("%s/%s.csv" % (target_dir, desired_name), 'wb') as f:
        dw = unicodecsv.DictWriter(f, keys, dialect='ALM')
        dw.writeheader()
        if type(data_to_write) == dict:
            dw.writerow(d)
        if type(data_to_write) == list:
            dw.writerows(d)
    f.close()
    
  def set_hitters(self, team_code):
    
    address = 'http://fantasysports.yahooapis.com/fantasy/v2/team/%s/roster' % team_code
    date = '2015-06-06'
    hit1key = '346.p.9719'
    hit2key = '346.p.8171'
    pos1 = 'OF'
    pos2 = 'BN'
    response = self.put(address, date, hit1key, hit2key, pos1, pos2)
    return None
    
    
    
    
    
    
    
      
      