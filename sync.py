#!/usr/local/bin/python3
'''
Author: Pascal Schlumpf (ps469x@att.com)

Description:

    Takes all the users from Active Directory and creates users for NagiosXI
'''



import urllib, json, httplib, socket, ldap, ConfigParser, base64

# this function makes the http call easier. you can provide a couple arguments such as method, host, url, body and cookie.
# Methods such as GET, POST, DELETE
# Body represents the payload in POST methods. For GET or DETELE they can be blank. body is optional
# Cookie is optional. Should be a string
def httpCall(method, host, url, body="", cookie=""):
	# set timeout to 30 seconds
	socket.setdefaulttimeout(30)
	# set default header for nagios
	headers = {"Content-Type": "application/x-www-form-urlencoded"}
	conn = httplib.HTTPConnection(host)
	headers["cookie"] = cookie
	conn.request(method, url, body, headers) 
	resp = conn.getresponse()
	content = resp.read()
	# get cookies for future use, such as authentication
	cookie = resp.getheader("set-cookie")

	return content, resp.status, cookie

# this function should make the extraction of Strings within Strings easier
def substr(searchString, startTag, endTag):
	result = ""
	searchString = searchString[searchString.find(startTag)+len(startTag):]
	result = searchString[: searchString.find(endTag)]
	return result;


def ldapCall(filter):
	try:
		l = ldap.initialize("ldaps://"+ldapServer+":636")
		l.protocol_version = ldap.VERSION3
		username = ldapUser
		password  = ldapPassword
		l.simple_bind(username, password)
		l.result()
		print "binding to ldap succesful"
	except ldap.LDAPError, e:
		print e

	# we want those attributes from AD to give to Nagios XI
	searchAttribute = ["mail","displayName", "sAMAccountName"]

	try:
		ldap_result_id = l.search(baseDn, ldap.SCOPE_SUBTREE, filter, searchAttribute)
		result_set = []
		while 1:
			result_type, result_data = l.result(ldap_result_id, 0)
			if (result_data == []):
				break
			else:
				if result_type == ldap.RES_SEARCH_ENTRY:
					result_set.append(result_data)

	except ldap.LDAPError, e:
		print e
	l.unbind_s()

	# put data in structure and return
	dic = {}
	for item in result_set:
		for pew in item:
			dic[pew[1]["sAMAccountName"][0]] = {"sAMAccountName": pew[1]["sAMAccountName"][0], "email": pew[1]["mail"][0], "name": pew[1]["displayName"][0], "addTag": True}

	return dic

# adding list of users, - flag indicates if user list is admin or regular user - path specify wether user list has admin or user privileges
def addUsers(dic, flag, path):
	for item in dic:
		print item
		if(dic[item]["addTag"]):
			print "marked for adding: " + item
			print "POST: " + host + baseUrlPhp + " | "+ postPath1+nsp_str+postPath2+urllib.quote(item)+postPath3+urllib.quote(flag)+urllib.quote(dic[item]["name"])+postPath4+urllib.quote(dic[item]["email"])+postPath5+adValue+postPath6+item+path
			_, status, _ = httpCall("POST", host, baseUrlPhp, postPath1+nsp_str+postPath2+urllib.quote(item)+postPath3+urllib.quote(flag)+urllib.quote(dic[item]["name"])+postPath4+urllib.quote(dic[item]["email"])+postPath5+adValue+postPath6+item+path, cookie)
			print "added user: ", status, cookie, nsp_str
		else:
			print "found, nothing to do: " + item



## start
#reading configs, path specified in install script
configParser = ConfigParser.RawConfigParser()   
configFilePath = r'/tmp/nagiosXiConfig'
configParser.read(configFilePath)

# initializing variables
host 			= configParser.get('DEFAULT', 'host')
basePath 		= "/nagiosxi/api/v1/system/user"
apikeyString 	= "?apikey="+configParser.get('DEFAULT', 'apikey')+"&pretty=1"
url 			= basePath + apikeyString
baseUrlPhp 		= "/nagiosxi/admin/users.php?users&edit=1"
loginBase 		= "/nagiosxi/login.php"
adminFilter 	= configParser.get('DEFAULT', 'adminFilter')
userFilter 		= configParser.get('DEFAULT', 'userFilter')
baseDn 			= configParser.get('DEFAULT', 'baseDn')
ldapUser		= configParser.get('DEFAULT', 'ldapUser')
ldapPassword	= configParser.get('DEFAULT', 'ldapPass')
postPath1		= configParser.get('DEFAULT', 'postPath1')
postPath2		= configParser.get('DEFAULT', 'postPath2')
postPath3		= configParser.get('DEFAULT', 'postPath3')
postPath4		= configParser.get('DEFAULT', 'postPath4')
postPath5		= configParser.get('DEFAULT', 'postPath5')
postPath6		= configParser.get('DEFAULT', 'postPath6')
postPathAdmin	= configParser.get('DEFAULT', 'postPathAdmin')
postPathUser	= configParser.get('DEFAULT', 'postPathUser')
ldapServer		= configParser.get('DEFAULT', 'ldapServer')
nagiosUser 		= configParser.get('DEFAULT', 'nagiosUser')
nagiosPass 		= configParser.get('DEFAULT', 'nagiosPass')

# initial get for login, store nsp and cookies
content, status, cookie = httpCall("GET", host, loginBase)
if (status == 200):
	nsp_str = substr(content, 'nsp_str = "', '";')
	if (len(nsp_str) != 64):
		print "something ain't right"

# logging in with credentials to "activate" cookie and nsp
_, status, _ = httpCall("POST", host, loginBase, "nsp="+nsp_str+"&page=auth&debug=&pageopt=login&username="+nagiosUser+"&password="+base64.b64decode(nagiosPass)+"&loginButton=", cookie)
if (status == 200 or status == 302):
	print "authenticated, ready to post"

#getting the ad server ids
content, status, cookie = httpCall("GET", host, "/nagiosxi/admin/users.php?users&edit=1", "", cookie)
if (status == 200 or status == 302):
	adValue = substr(substr(content, '<select name="ad_server" class="form-control">', "</select>"), 'value="', '"');


# call to get users
content, _, _ = httpCall("GET", host, url)
data = json.loads(content)

#convert users into dictionary
deleteDic = {}
for item in data["users"]:
	deleteDic[item["username"]] = {"userId": item["user_id"], "name": item["name"], "deleteTag": True};

ldapAdminDic = ldapCall(adminFilter)
ldapUserDic = ldapCall(userFilter)


## core logic
# going thru both (3 respectively) sets of data and flagging them
for item in deleteDic:
	for username in ldapAdminDic:
		# user in ldap admin group matches user in nagios
		if(item == username):
			# if user also matches privileges user (U) we can tag them as delete from nagios
			if(deleteDic[item]["name"][0:3] == "(U)"):
				deleteDic[username]["deleteTag"] = True
				ldapUserDic[username]["addTag"] = False
			# if user matches privileges admin (A) we're good, nothing to do
			elif(deleteDic[item]["name"][0:3] == "(A)"):
				deleteDic[username]["deleteTag"] = False
				ldapAdminDic[username]["addTag"] = False
				# if user that is in ldap admin group and has nagios admin rights is also in the ldap user group, we can flag him not to be added as a user
				if username in ldapUserDic.keys():
					ldapUserDic[username]["addTag"] = False
			# if neither privileges are set, we can flag user to be deleted
			else:
				deleteDic[username]["deleteTag"] = True
	for username in ldapUserDic:
		# if user has not been flagged as don't add (line 170, ldapUserDic[username]["addTag"] = False) AND user is found in nagios AND user has privileges user, nothing needs to be done
		if(ldapUserDic[username]["addTag"] and item == username and deleteDic[item]["name"][0:3] == "(U)"):
			deleteDic[username]["deleteTag"] = False
			ldapUserDic[username]["addTag"] = False

# going thru all the users that were flagged for deleteion
for item in deleteDic:
	if(deleteDic[item]["deleteTag"] and item != "nagiosadmin" and item != "honeybadgers"):
		print "marked for deletion: " + item
		delURL = "http://" + host + basePath + "/" + deleteDic[item]["userId"] + apikeyString
		print delURL
		httpCall("DELETE", host, basePath + "/" + deleteDic[item]["userId"] + apikeyString,)

# adding users from both user groups
addUsers(ldapAdminDic, "(A) ", postPathAdmin)
addUsers(ldapUserDic, "(U) ", postPathUser)