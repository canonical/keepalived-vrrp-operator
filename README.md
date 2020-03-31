# Overview

The purpose of this charm is to set up keepalived based on the parameters passed in from a primary charm to provide virtual IP functionality via VRRP protocol.

A charm of a primary app needs to implement vrrp-parameters interface and pass configuration such as a virtual IP, interface name, virtual router id, health-check scripts to use and other relevant configuration for VRRP instances. When multiple units of a primary app are deployed, they will each get a subordinate keepalived unit that may hold a VIP depending on the current protocol state.

# Restrictions

All units of a primary application need to be in the same L2 broadcast domain because the failover mechanism depends on GARP (gratuitous ARP).

# Usage

```
juju deploy <primary-charm> -n 3
juju deploy keepalived
juju relate <primary-charm> keepalived
```
