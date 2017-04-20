## Description
Nagios XI does provide LDAP/AD support from the box, however, it does not integrate with groups or users to LDAP/AD specifically. To circumvent that, we created a script that checks the AD for users and syncs them with Nagios XI.

## Usage
This repo is supposed to be installed and then work automatically. To install, run the `install.sh`. The script takes a couple arguments:
- apikey
- host
- adminFilter
- userFilter
- baseDn
- DC
- ldapServer

From there it creates a cronjob, that runs every hour and creates the configuration file that the python script reads during execution.

## Contact
We have written several Confluence pages about Nagios; check out [this page](http://egconfluence.dtveng.net/display/DFWQL/Nagios) and it's child pages. If you still have any questions about Nagios or anything in this repo feel free to contact Nick Gibson (ng560p@att.com), Jon De Leon (wd195u@att.com), or Pascal Schlumpf (ps469x@att.com). If you have questions about the sync script contact Pascal.