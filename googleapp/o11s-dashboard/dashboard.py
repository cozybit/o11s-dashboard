# vim:set ts=4 sw=4:
#
# Copyright (c) 2012 cozybit Inc.
#
#	This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import string
import logging
 
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import namespace_manager

def local_nets_key():
	return db.Key.from_path('MeshNetwork', 'o11s_networks')

def list_of_networks():
		return MeshNetwork.gql("WHERE ANCESTOR IS :1 " 
						   		"ORDER BY date DESC", 
								local_nets_key() )
# Data model is as follows:
# 
# MeshNetwork 1-----* Mesh Nodes (in Datastore) 
#
# Each MeshNetwork is a unique namespace.
#                           
class MeshNetwork(db.Model):
	"""Models individual mesh networks keyed by <network id>"""
	netid = db.StringListProperty()
	date = db.DateTimeProperty(auto_now_add=True)

class MeshNode(db.Model):
	"""Models mesh point"""
	mac = db.StringListProperty()
	lat = db.FloatProperty()
	lon = db.FloatProperty()

class MainPage(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write('Main Page.  Nothing here')

class AddNet(webapp.RequestHandler):
	def get(self):
		netid = self.request.str_params['netid']
		logging.info('netid: ' + netid)
		if netid == None:
			self.error(400);
			return
		# Check for existence first
		net = MeshNetwork.get_by_key_name(netid, parent = local_nets_key())
		if net == None:
			net = MeshNetwork( key_name = netid, 
								parent = local_nets_key())
			net.put()
		else:	
			logging.error("DUP NETID")
			self.error(400);
		return

class ListNets(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		for net in list_of_networks():
			self.response.out.write('network:' + '\n')
			self.response.out.write(net.key().name() + '\n')
			self.response.out.write(str(net.date) + '\n')

application = webapp.WSGIApplication(
									[
										('/', MainPage),
									  	('/addnetwork', AddNet),
#									  	('/addnode', Register),
									  	('/list', ListNets),
#									  	('/checkin', RecordPoint),
									],
									 debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
