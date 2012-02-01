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
import os
import random
import re
import datetime
 
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import namespace_manager

def local_nets_key():
	return db.Key.from_path('MeshNetwork', 'o11s_networks')

def list_of_networks():
	return MeshNetwork.gql("WHERE ANCESTOR IS :1 " 
						   		"ORDER BY date DESC", 
								local_nets_key() )

def list_of_mesh_nodes():
	"""List of mesh nodes on a given network namespace."""
	return MeshNode.gql("")

def switch_namespace(netid):
	if netid == None:
		self.error(400);
		return False

	net = MeshNetwork.get_by_key_name(netid, parent = local_nets_key())
	if net == None:
		self.error(400);
		return False
	namespace_manager.set_namespace(net.key().name());
	return True

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
	last_seen = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write('Main Page.  Nothing here')

class AddNet(webapp.RequestHandler):
	def get(self):
		self.response.out.write("""
			<html>
				<body>
					<form action="/addnetwork" method="post">
						<div><input type=text name="netid"></input></div>
						<div><input type="submit" value="Add Network"></div>
					</form>
				</body>
			</html>""")
		return

	def post(self):
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
			self.redirect("/list")

		else:	
			self.error(400);
		return

class ListNets(webapp.RequestHandler):
	def get(self):
		template_values = {
			'nets': list_of_networks(),
		}
		path = os.path.join(os.path.dirname(__file__), "net.html")
		self.response.out.write(template.render(path, template_values))

def validate(addr):
		try:
			s=re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', addr, re.I).group()
			return True
		except:
			return False
		
class CheckIn(webapp.RequestHandler):
	def get(self):
		# Maybe some tiny embedded nodes don't support post so accept
		# GET checkins as well.
		self.post()

	def post(self):
		netid = self.request.str_params['netid']
		if not switch_namespace(netid):
			self.error(400);
			return

		macaddr = self.request.str_params['macaddr']
		if not validate(macaddr):
			self.error(400);
			return

		node = MeshNode.get_by_key_name(macaddr);
		node.last_seen = datetime.datetime.now()
		node.put()
		return

class AddNode(webapp.RequestHandler):
	def get(self):
		# netid is optional in this case
		netid = self.request.str_params['netid']
		template_values = {
			'nets': list_of_networks(),
			'netid': netid,
		}
		path = os.path.join(os.path.dirname(__file__), "addnode.html")
		self.response.out.write(template.render(path, template_values))
		return

	def post(self):
		netid = self.request.str_params['netid']
		if not switch_namespace(netid):
			self.error(400);
			return

		macaddr = self.request.str_params['macaddr']
		if not validate(macaddr):
			self.error(400);
			return

		node = MeshNode(key_name = macaddr, lat = random.random(), lon = random.random());
		node.put()
		self.redirect('/listnodes?netid=' + netid)

class ListNodes(webapp.RequestHandler):
	def get(self):
		netid = self.request.str_params['netid']
		if not switch_namespace(netid):
			self.error(400);
			return

		template_values = {
			'nodes': list_of_mesh_nodes(),
			'netid' : netid,
		}
		path = os.path.join(os.path.dirname(__file__), "nodes.html")
		self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
									[
										('/', MainPage),
									  	('/addnetwork', AddNet),
									  	('/addnode', AddNode),
									  	('/list', ListNets),
									  	('/listnodes', ListNodes),
									  	('/checkin', CheckIn),
									],
									 debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
