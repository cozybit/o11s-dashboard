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
import math
import copy
 
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
	lng = db.FloatProperty()
	last_seen = db.DateTimeProperty(auto_now_add=True)
	peers = db.ListProperty(db.Key);

class MainPage(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write('Main Page.  Nothing here')

class AddNet(webapp.RequestHandler):
	def get(self):
		self.response.out.write("""
			<html>
				<body>
					Please, no spaces or strange characters...<br/>
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
		if netid == None or not validate_netid(netid):
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

def validate_mac(addr):
		return re.match(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', addr, re.I) != None

def validate_netid(netid):
		return re.match(r'^[0-9A-Za-z._-]{0,100}$', netid, re.I) != None
		
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

		macaddr = self.request.str_params['macaddr'].lower()
		if not validate_mac(macaddr):
			self.error(400);
			return

		node = MeshNode.get_by_key_name(macaddr);
		node.last_seen = datetime.datetime.now()
		peers = self.request.str_params.getall("peer")
		node.peers = []
		for p in peers:
			if not validate_mac(p):
				continue
			peer = MeshNode.get_by_key_name(p);
			if peer != None:
				node.peers.append(peer.key())
		node.put()
		return

class AddNode(webapp.RequestHandler):
	def get(self):
		# netid is optional in this case
		netid = self.request.str_params['netid']
		lat = self.request.str_params['lat']
		lng = self.request.str_params['lng']
		template_values = {
			'nets': list_of_networks(),
			'netid': netid,
			'lat' : lat,
			'lng' : lng,
		}
		path = os.path.join(os.path.dirname(__file__), "addnode.html")
		self.response.out.write(template.render(path, template_values))
		return

	def post(self):
		netid = self.request.str_params['netid']
		if not switch_namespace(netid):
			self.error(400);
			return

		macaddr = self.request.str_params['macaddr'].lower()
		if not validate_mac(macaddr):
			self.error(400);
			return

		lat = float(self.request.str_params['lat'])
		lng = float(self.request.str_params['lng'])

		node = MeshNode(key_name = macaddr, lat = lat, lng = lng);
		node.put()
		self.redirect('/listnodes?netid=' + netid)

def split_links(link):
	''' Nudge links one direction or another so that symmetic links are displayed as double lines '''
	# calculate the slope in units of length, not degrees, which depends on latitude
	delta_lat = link[0].lat - link[1].lat
	delta_lng = (link[0].lng - link[1].lng) * math.cos(math.radians(link[0].lat))
	link_len = math.sqrt(delta_lat**2 + delta_lng**2)
	if (delta_lat):
		slope = -float(delta_lng / delta_lat)
	else:
		slope = float('inf')	
	if (delta_lat != 0):
		offset = cmp(delta_lat,0) * link_len/40
	else:
		offset = cmp(delta_lng,0) * link_len/40
	link[0].lat += offset*math.sin(math.atan(slope))
	link[1].lat += offset*math.sin(math.atan(slope)) 
	link[0].lng += offset*math.cos(math.atan(slope))
	link[1].lng += offset*math.cos(math.atan(slope))
	return link

class ListNodes(webapp.RequestHandler):
	def get(self):
		netid = self.request.str_params['netid']
		if not switch_namespace(netid):
			self.error(400);
			return

		links = []
		for node in list_of_mesh_nodes():
			for p in node.peers:
				peer = MeshNode.get(p)
				if (peer != None):
					link = split_links([copy.copy(node), copy.copy(peer)])
					links.append(link)

		template_values = {
			'nodes': list_of_mesh_nodes(),
			'netid' : netid,
			'now' : datetime.datetime.now(),
			'links' : links,
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
