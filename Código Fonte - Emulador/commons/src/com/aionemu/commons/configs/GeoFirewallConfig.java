package com.aionemu.commons.configs;

import com.aionemu.commons.configuration.Property;

/**
 * Geographic Firewall configuration mapped from geo_firewall.properties.
 * 
 * @author Lost Academy Team & Durak
 */
public class GeoFirewallConfig {

	@Property(key = "geo.firewall.enable", defaultValue = "false")
	public static boolean GEO_FIREWALL_ENABLE;

	@Property(key = "geo.firewall.world_ip_range_dir", defaultValue = "")
	public static String GEO_FIREWALL_DATA_DIR;

	@Property(key = "geo.firewall.allowed_countries", defaultValue = "all")
	public static String GEO_FIREWALL_ALLOWED_COUNTRIES;

	@Property(key = "geo.firewall.manual_whitelist_ips", defaultValue = "")
	public static String GEO_FIREWALL_MANUAL_WHITELIST_IPS;
}
