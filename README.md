# GROS visualization proxy and site

This repository contains configuration files and static web files for the 
visualization hub of the GROS project within ICTU. The proxy is intended to 
provide access to a Ghost blog and Discourse forum, as well as to the 
visualization reports generated within a Jenkins instance.

The repository contains ICTU-specific addresses and is not suitable for use 
outside the ICTU environment. Two stages of reverse proxies are used to safely 
provide access to the GROS VLAN. The reverse proxies are as follows:

- [Caddy](https://caddyserver.com/) for transparent proxy access from a BigBoat 
  dashboard. Several subinstances handle specific domain names.
- [NGINX](https://www.nginx.com/) for proxy access and static file hosting from 
  a central server listening on specific ports as well as using Host-based 
  proxying.

See the 
[Wiki](http://www.wiki.gros.test/index.php/Upload-server_specifications) 
for more details on how the second proxy layer works.
