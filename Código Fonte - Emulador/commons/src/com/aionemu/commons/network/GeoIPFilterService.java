package com.aionemu.commons.network;

import com.aionemu.commons.configs.GeoFirewallConfig;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.Inet4Address;
import java.net.Inet6Address;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * @author Lost Academy Team & Durak
 *
 * Geographic Firewall & IP Allow-list Service.
 * <p>
 * Controls allowed incoming connections across LoginServer, GameServer, and ChatServer.
 * Lookups at runtime are lock-free and allocation-free.
 * <p>
 * Configurable via `config/network/geo_firewall.properties`:
 * - geo.firewall.enable (boolean, default false)
 * - geo.firewall.world_ip_range_dir (directory path for WORLD IP RANGE)
 * - geo.firewall.allowed_countries (comma-separated ISO 2-letter codes or "all")
 * - geo.firewall.manual_whitelist_ips (comma-separated IP or CIDR ranges)
 */
public final class GeoIPFilterService {

	private static final Logger log = LoggerFactory.getLogger(GeoIPFilterService.class);

	// ── Directory / file names ────────────────────────────────────────────────
	private static final String GEOIP_DIR_NAME              = "GeoIP";
	private static final String WORLD_IP_RANGE_DIR_NAME     = "WORLD IP RANGE";
	private static final String DIR_ALL_ZONES               = "all-zones";
	private static final String DIR_IPV6_ALL_ZONES          = "ipv6-all-zones";
	private static final String DIR_ONLY_SOUTH_AMERICA      = "only south america";
	private static final String DIR_ALLOWED_REGIONS         = "allowed regions";
	private static final String FILE_MANUAL_WHITELIST       = "manual-whitelist.zone";
	private static final String DIR_GEOIP_CACHE             = ".geoip-cache";
	private static final String FILE_GEOIP_CACHE_SNAPSHOT   = "geo_firewall.snapshot.bin";
	private static final String FILE_GEOIP_CACHE_TMP        = "geo_firewall.snapshot.bin.tmp";

	// ── Configuration properties ──────────────────────────────────────────────
	private static final String CONFIG_FILE_PATH            = "./config/network/geo_firewall.properties";
	private static final String PROP_FIREWALL_ENABLE        = "geo.firewall.enable";
	private static final String PROP_WORLD_IP_RANGE_DIR     = "geo.firewall.world_ip_range_dir";
	private static final String PROP_ALLOWED_COUNTRIES      = "geo.firewall.allowed_countries";
	private static final String PROP_MANUAL_WHITELIST_IPS   = "geo.firewall.manual_whitelist_ips";

	// ── System-property / env overrides ──────────────────────────────────────
	private static final String SYS_PROP_WORLD_IP_RANGE_DIR = "geoip.world.range.dir";
	private static final String ENV_WORLD_IP_RANGE_DIR      = "GEOIP_WORLD_RANGE_DIR";

	// ── Binary-cache format ───────────────────────────────────────────────────
	private static final int CACHE_MAGIC                    = 0x47495046; // "GIPF"
	private static final int CACHE_VERSION                  = 2;
	private static final int MAX_ALLOWED_RANGES_IN_CACHE    = 15_000_000;

	// ── State ─────────────────────────────────────────────────────────────────
	private static final AtomicBoolean loaded = new AtomicBoolean(false);
	private static final Object loadLock      = new Object();
	private static volatile boolean enabled   = false;
	private static volatile Snapshot snapshot = Snapshot.DENY_ALL;

	private GeoIPFilterService() {}

	// ══════════════════════════════════════════════════════════════════════════
	// Public API
	// ══════════════════════════════════════════════════════════════════════════

	public static void load() {
		load(null);
	}

	public static void load(Properties externalProps) {
		synchronized (loadLock) {
			long startedAt = System.nanoTime();
			Properties props = loadProperties(externalProps);
			enabled = Boolean.parseBoolean(props.getProperty(PROP_FIREWALL_ENABLE, "false").trim());

			if (!enabled) {
				snapshot = Snapshot.ALLOW_ALL;
				loaded.set(true);
				log.info("GeoIP Firewall is DISABLED (geo.firewall.enable=false). All incoming connections are permitted.");
				return;
			}

			try {
				Snapshot next = buildSnapshot(props);
				snapshot = next;
				loaded.set(true);
				double ms = (System.nanoTime() - startedAt) / 1_000_000.0;
				log.info("GeoIP Firewall ENABLED: {} IPv4 ranges, {} IPv6 ranges loaded from '{}', took {} ms",
					next.ipv4RangesCount, next.ipv6RangesCount, next.sourcePath,
					String.format(Locale.ROOT, "%.2f", ms));
				log.info("GeoIP benchmark: {}", benchmark(next));
			} catch (Exception e) {
				snapshot = Snapshot.DENY_ALL;
				loaded.set(true);
				log.error("GeoIP Firewall load failed — defaulting to DENY-ALL for non-local addresses for safety!", e);
			}
		}
	}

	public static void reload() {
		load();
	}

	public static boolean isEnabled() {
		return enabled;
	}

	/**
	 * Returns true if the given IP string is permitted.
	 */
	public static boolean isAllowed(String ip) {
		if (ip == null || ip.isEmpty())
			return false;
		if (!enabled)
			return true;
		ensureLoaded();
		try {
			int ipv4 = parseIpv4(ip);
			if (ipv4 >= 0) {
				long unsignedIp = ipv4 & 0xFFFFFFFFL;
				if (isPrivateIpv4(unsignedIp))
					return true;
				return isAllowedIpv4Unsigned(unsignedIp, snapshot);
			}
			return isAllowed(InetAddress.getByName(ip));
		} catch (Exception ignored) {
			return false;
		}
	}

	/**
	 * Returns true if the given InetAddress is permitted.
	 */
	public static boolean isAllowed(InetAddress address) {
		if (address == null)
			return false;
		if (!enabled)
			return true;
		ensureLoaded();
		if (isAlwaysAllowed(address))
			return true;

		Snapshot s = snapshot;
		if (s == Snapshot.ALLOW_ALL)
			return true;
		if (s == Snapshot.DENY_ALL)
			return false;

		return switch (address) {
			case Inet4Address v4 -> {
				long ip = ipv4ToUnsignedLong(v4.getAddress(), 0);
				yield isAllowedIpv4Unsigned(ip, s);
			}
			case Inet6Address v6 -> {
				byte[] bytes = v6.getAddress();
				if (isIpv4MappedIpv6(bytes))
					yield isAllowedIpv4Unsigned(ipv4ToUnsignedLong(bytes, 12), s);
				yield isAllowedIpv6(bytes, s);
			}
			default -> false;
		};
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Configuration Loading
	// ══════════════════════════════════════════════════════════════════════════

	private static Properties loadProperties(Properties externalProps) {
		Properties props = new Properties();
		if (externalProps != null) {
			props.putAll(externalProps);
		}

		File cfgFile = new File(CONFIG_FILE_PATH);
		if (cfgFile.isFile()) {
			try (InputStream in = new FileInputStream(cfgFile)) {
				props.load(in);
				log.info("GeoIP: loaded configuration from {}", cfgFile.getAbsolutePath());
			} catch (Exception e) {
				log.warn("GeoIP: could not read {}: {}", CONFIG_FILE_PATH, e.getMessage());
			}
		} else {
			File altFile = new File("geo_firewall.properties");
			if (altFile.isFile()) {
				try (InputStream in = new FileInputStream(altFile)) {
					props.load(in);
					log.info("GeoIP: loaded configuration from {}", altFile.getAbsolutePath());
				} catch (Exception e) {
					log.warn("GeoIP: could not read {}: {}", altFile.getName(), e.getMessage());
				}
			}
		}

		if (GeoFirewallConfig.GEO_FIREWALL_ENABLE || !props.containsKey(PROP_FIREWALL_ENABLE)) {
			if (GeoFirewallConfig.GEO_FIREWALL_ENABLE) {
				props.setProperty(PROP_FIREWALL_ENABLE, "true");
			}
		}
		if (GeoFirewallConfig.GEO_FIREWALL_DATA_DIR != null && !GeoFirewallConfig.GEO_FIREWALL_DATA_DIR.isBlank()) {
			props.setProperty(PROP_WORLD_IP_RANGE_DIR, GeoFirewallConfig.GEO_FIREWALL_DATA_DIR);
		}
		if (GeoFirewallConfig.GEO_FIREWALL_ALLOWED_COUNTRIES != null && !GeoFirewallConfig.GEO_FIREWALL_ALLOWED_COUNTRIES.isBlank()) {
			props.setProperty(PROP_ALLOWED_COUNTRIES, GeoFirewallConfig.GEO_FIREWALL_ALLOWED_COUNTRIES);
		}
		if (GeoFirewallConfig.GEO_FIREWALL_MANUAL_WHITELIST_IPS != null && !GeoFirewallConfig.GEO_FIREWALL_MANUAL_WHITELIST_IPS.isBlank()) {
			props.setProperty(PROP_MANUAL_WHITELIST_IPS, GeoFirewallConfig.GEO_FIREWALL_MANUAL_WHITELIST_IPS);
		}

		GeoFirewallConfig.GEO_FIREWALL_ENABLE = Boolean.parseBoolean(props.getProperty(PROP_FIREWALL_ENABLE, "false").trim());
		GeoFirewallConfig.GEO_FIREWALL_DATA_DIR = props.getProperty(PROP_WORLD_IP_RANGE_DIR, "");
		GeoFirewallConfig.GEO_FIREWALL_ALLOWED_COUNTRIES = props.getProperty(PROP_ALLOWED_COUNTRIES, "all");
		GeoFirewallConfig.GEO_FIREWALL_MANUAL_WHITELIST_IPS = props.getProperty(PROP_MANUAL_WHITELIST_IPS, "");

		return props;
	}

	private static void ensureLoaded() {
		if (!loaded.get())
			load();
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Directory Resolution
	// ══════════════════════════════════════════════════════════════════════════

	private static Path resolveWorldIpRangeDir(String customPath) {
		// 1 - Custom path from properties
		if (customPath != null && !customPath.isBlank()) {
			Path p = Path.of(customPath.trim()).toAbsolutePath().normalize();
			if (Files.isDirectory(p)) return p;
			log.warn("GeoIP: configured path '{}' does not exist or is not a directory: {}", PROP_WORLD_IP_RANGE_DIR, p);
		}

		// 2 - System property
		String prop = System.getProperty(SYS_PROP_WORLD_IP_RANGE_DIR);
		if (prop != null && !prop.isBlank()) {
			Path p = Path.of(prop.trim()).toAbsolutePath().normalize();
			if (Files.isDirectory(p)) return p;
		}

		// 3 - Environment variable
		String env = System.getenv(ENV_WORLD_IP_RANGE_DIR);
		if (env != null && !env.isBlank()) {
			Path p = Path.of(env.trim()).toAbsolutePath().normalize();
			if (Files.isDirectory(p)) return p;
		}

		// 4 - Search candidates relative to cwd (Config/GeoIP, GeoIP, and legacy WORLD IP RANGE)
		Path[] candidates = {
			// New standard layout: Config/GeoIP
			Path.of("Config", GEOIP_DIR_NAME).toAbsolutePath().normalize(),
			Path.of("..", "Config", GEOIP_DIR_NAME).toAbsolutePath().normalize(),
			Path.of("..", "..", "Config", GEOIP_DIR_NAME).toAbsolutePath().normalize(),
			// Direct GeoIP layout
			Path.of(GEOIP_DIR_NAME).toAbsolutePath().normalize(),
			Path.of("..", GEOIP_DIR_NAME).toAbsolutePath().normalize(),
			Path.of("..", "..", GEOIP_DIR_NAME).toAbsolutePath().normalize(),
			// Legacy fallback layout
			Path.of(WORLD_IP_RANGE_DIR_NAME).toAbsolutePath().normalize(),
			Path.of("..", WORLD_IP_RANGE_DIR_NAME).toAbsolutePath().normalize(),
			Path.of("..", "..", WORLD_IP_RANGE_DIR_NAME).toAbsolutePath().normalize()
		};

		for (Path c : candidates) {
			if (Files.isDirectory(c))
				return c;
		}

		return null;
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Snapshot construction
	// ══════════════════════════════════════════════════════════════════════════

	private static Snapshot buildSnapshot(Properties props) throws IOException {
		String customDir = props.getProperty(PROP_WORLD_IP_RANGE_DIR, "");
		Path baseDir = resolveWorldIpRangeDir(customDir);
		if (baseDir == null) {
			throw new IOException("WORLD IP RANGE directory not found! Ensure directory exists or configure '"
				+ PROP_WORLD_IP_RANGE_DIR + "' in " + CONFIG_FILE_PATH);
		}

		String allowedCountriesStr = props.getProperty(PROP_ALLOWED_COUNTRIES, "br,ar,cl,uy,py,bo,co,ec,pe,ve,gy,sr,gf,fk").trim();
		String manualWhitelistIpsStr = props.getProperty(PROP_MANUAL_WHITELIST_IPS, "").trim();

		List<Path> zoneFiles = collectZoneFiles(baseDir, allowedCountriesStr);
		long signature = computeSnapshotSignature(zoneFiles, allowedCountriesStr, manualWhitelistIpsStr);

		Snapshot cached = tryLoadSnapshotFromCache(baseDir, signature);
		if (cached != null) {
			return cached;
		}

		List<LongRange> ipv4Ranges = new ArrayList<>();
		List<Ipv6Range> ipv6Ranges = new ArrayList<>();

		// 1 - Load parsed country zone files
		for (Path zoneFile : zoneFiles) {
			loadZoneFile(zoneFile, ipv4Ranges, ipv6Ranges);
		}

		// 2 - Load manual whitelist file if exists
		Path manualFile = baseDir.resolve(FILE_MANUAL_WHITELIST);
		if (Files.isRegularFile(manualFile)) {
			loadZoneFile(manualFile, ipv4Ranges, ipv6Ranges);
		}

		// 3 - Load manual whitelist IPs from properties
		if (!manualWhitelistIpsStr.isEmpty()) {
			parseManualWhitelistProperties(manualWhitelistIpsStr, ipv4Ranges, ipv6Ranges);
		}

		normalizeIpv4Ranges(ipv4Ranges);
		normalizeIpv6Ranges(ipv6Ranges);

		Snapshot parsed = Snapshot.from(baseDir + " (" + allowedCountriesStr + ")", ipv4Ranges, ipv6Ranges);
		writeSnapshotCache(baseDir, signature, parsed);
		return parsed;
	}

	private static List<Path> collectZoneFiles(Path baseDir, String allowedCountriesStr) throws IOException {
		List<Path> zoneFiles = new ArrayList<>();
		boolean allowAll = allowedCountriesStr.equalsIgnoreCase("all") || allowedCountriesStr.equals("*");

		Set<String> countryCodes = new HashSet<>();
		if (!allowAll) {
			for (String code : allowedCountriesStr.split("[,;\\s]+")) {
				String c = code.trim().toLowerCase(Locale.ROOT);
				if (!c.isEmpty())
					countryCodes.add(c);
			}
		}

		Path allZonesDir = baseDir.resolve(DIR_ALL_ZONES);
		Path ipv6AllZonesDir = baseDir.resolve(DIR_IPV6_ALL_ZONES);
		Path onlySouthAmericaDir = baseDir.resolve(DIR_ONLY_SOUTH_AMERICA);
		Path allowedRegionsDir = baseDir.resolve(DIR_ALLOWED_REGIONS);

		if (allowAll) {
			if (Files.isDirectory(allZonesDir)) {
				try (DirectoryStream<Path> stream = Files.newDirectoryStream(allZonesDir, "*.zone")) {
					for (Path file : stream)
						if (Files.isRegularFile(file)) zoneFiles.add(file.toAbsolutePath().normalize());
				}
			}
			if (Files.isDirectory(ipv6AllZonesDir)) {
				try (DirectoryStream<Path> stream = Files.newDirectoryStream(ipv6AllZonesDir, "*.zone")) {
					for (Path file : stream)
						if (Files.isRegularFile(file)) zoneFiles.add(file.toAbsolutePath().normalize());
				}
			}
		} else {
			for (String code : countryCodes) {
				boolean foundV4 = false;
				if (Files.isDirectory(allZonesDir)) {
					Path f = allZonesDir.resolve(code + ".zone");
					if (Files.isRegularFile(f)) {
						zoneFiles.add(f.toAbsolutePath().normalize());
						foundV4 = true;
					}
				}
				if (!foundV4 && Files.isDirectory(onlySouthAmericaDir)) {
					Path f = onlySouthAmericaDir.resolve(code + ".zone");
					if (Files.isRegularFile(f)) {
						zoneFiles.add(f.toAbsolutePath().normalize());
					}
				}
				if (!foundV4 && Files.isDirectory(allowedRegionsDir)) {
					try (DirectoryStream<Path> subDirs = Files.newDirectoryStream(allowedRegionsDir)) {
						for (Path sub : subDirs) {
							if (Files.isDirectory(sub)) {
								Path f = sub.resolve(code + ".zone");
								if (Files.isRegularFile(f)) {
									zoneFiles.add(f.toAbsolutePath().normalize());
									break;
								}
							}
						}
					}
				}

				// IPv6
				if (Files.isDirectory(ipv6AllZonesDir)) {
					Path f6 = ipv6AllZonesDir.resolve(code + ".zone");
					if (Files.isRegularFile(f6)) {
						zoneFiles.add(f6.toAbsolutePath().normalize());
					}
				}
			}
		}

		zoneFiles.sort(Comparator.comparing(p -> p.toString().toLowerCase(Locale.ROOT)));
		return zoneFiles;
	}

	private static void parseManualWhitelistProperties(String whitelist, List<LongRange> ipv4Ranges, List<Ipv6Range> ipv6Ranges) {
		String[] tokens = whitelist.split("[,;\\s]+");
		for (String token : tokens) {
			String line = sanitize(token);
			if (line.isEmpty()) continue;

			int slash = line.indexOf('/');
			String ipPart = slash > 0 ? line.substring(0, slash).trim() : line;
			int prefix = slash > 0 ? Integer.parseInt(line.substring(slash + 1).trim()) : -1;

			if (ipPart.indexOf(':') >= 0) {
				// IPv6
				if (prefix < 0) prefix = 128;
				try {
					byte[] ip = InetAddress.getByName(ipPart).getAddress();
					if (ip.length == 16) {
						ipv6Ranges.add(ipv6RangeFromCidr(ip, prefix));
					}
				} catch (Exception ignored) {}
			} else {
				// IPv4
				if (prefix < 0) prefix = 32;
				int ip = parseIpv4(ipPart);
				if (ip >= 0) {
					long[] range = ipv4RangeFromCidr(ip, prefix);
					ipv4Ranges.add(new LongRange(range[0], range[1]));
				}
			}
		}
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Binary cache
	// ══════════════════════════════════════════════════════════════════════════

	private static long computeSnapshotSignature(List<Path> zoneFiles, String allowedCountries, String manualWhitelist) {
		long hash = 0xcbf29ce484222325L;
		// Hash configuration strings
		String cfgKey = allowedCountries.toLowerCase(Locale.ROOT) + "|" + manualWhitelist;
		for (int i = 0, len = cfgKey.length(); i < len; i++) {
			hash ^= cfgKey.charAt(i);
			hash *= 0x100000001b3L;
		}

		for (Path file : zoneFiles) {
			String key = file.toString().toLowerCase(Locale.ROOT);
			for (int i = 0, len = key.length(); i < len; i++) {
				hash ^= key.charAt(i);
				hash *= 0x100000001b3L;
			}
			try {
				hash ^= Files.size(file);
				hash *= 0x100000001b3L;
				hash ^= Files.getLastModifiedTime(file).toMillis();
				hash *= 0x100000001b3L;
			} catch (IOException e) {
				hash ^= System.nanoTime();
				hash *= 0x100000001b3L;
			}
		}
		hash ^= zoneFiles.size();
		hash *= 0x100000001b3L;
		return hash;
	}

	private static Snapshot tryLoadSnapshotFromCache(Path baseDir, long signature) {
		Path cacheFile = baseDir.resolve(DIR_GEOIP_CACHE).resolve(FILE_GEOIP_CACHE_SNAPSHOT);
		if (!Files.isRegularFile(cacheFile)) return null;

		try (var in = new DataInputStream(new BufferedInputStream(Files.newInputStream(cacheFile)))) {
			if (in.readInt() != CACHE_MAGIC || in.readInt() != CACHE_VERSION || in.readLong() != signature)
				return null;

			long[] ipv4Starts   = readLongArray(in);
			long[] ipv4Ends     = readLongArray(in);
			long[] ipv6StartsHi = readLongArray(in);
			long[] ipv6StartsLo = readLongArray(in);
			long[] ipv6EndsHi   = readLongArray(in);
			long[] ipv6EndsLo   = readLongArray(in);

			if (ipv4Starts.length != ipv4Ends.length
				|| ipv6StartsHi.length != ipv6StartsLo.length
				|| ipv6StartsHi.length != ipv6EndsHi.length
				|| ipv6StartsHi.length != ipv6EndsLo.length)
				return null;

			return Snapshot.fromArrays(baseDir + " (binary-cache)",
				ipv4Starts, ipv4Ends, ipv6StartsHi, ipv6StartsLo, ipv6EndsHi, ipv6EndsLo);
		} catch (Exception e) {
			log.warn("GeoIP cache unreadable — falling back to .zone parse: {}", cacheFile, e);
			return null;
		}
	}

	private static void writeSnapshotCache(Path baseDir, long signature, Snapshot s) {
		Path cacheDir  = baseDir.resolve(DIR_GEOIP_CACHE);
		Path tmpFile   = cacheDir.resolve(FILE_GEOIP_CACHE_TMP);
		Path finalFile = cacheDir.resolve(FILE_GEOIP_CACHE_SNAPSHOT);
		try {
			Files.createDirectories(cacheDir);
			try (var out = new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(tmpFile)))) {
				out.writeInt(CACHE_MAGIC);
				out.writeInt(CACHE_VERSION);
				out.writeLong(signature);
				writeLongArray(out, s.ipv4Starts);
				writeLongArray(out, s.ipv4Ends);
				writeLongArray(out, s.ipv6StartsHi);
				writeLongArray(out, s.ipv6StartsLo);
				writeLongArray(out, s.ipv6EndsHi);
				writeLongArray(out, s.ipv6EndsLo);
			}
			Files.move(tmpFile, finalFile, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
		} catch (Exception e) {
			log.warn("GeoIP cache write failed: {}", finalFile, e);
			try { Files.deleteIfExists(tmpFile); } catch (IOException ignored) {}
		}
	}

	private static void writeLongArray(DataOutputStream out, long[] values) throws IOException {
		out.writeInt(values.length);
		for (long v : values) out.writeLong(v);
	}

	private static long[] readLongArray(DataInputStream in) throws IOException {
		int len = in.readInt();
		if (len < 0 || len > MAX_ALLOWED_RANGES_IN_CACHE)
			throw new IOException("Invalid cache array length: " + len);
		long[] values = new long[len];
		for (int i = 0; i < len; i++) values[i] = in.readLong();
		return values;
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Zone-file parsing
	// ══════════════════════════════════════════════════════════════════════════

	private static void loadZoneFile(Path file, List<LongRange> ipv4Ranges, List<Ipv6Range> ipv6Ranges) throws IOException {
		try (var reader = new BufferedReader(new InputStreamReader(Files.newInputStream(file), StandardCharsets.UTF_8))) {
			String raw;
			int lineNo = 0;
			while ((raw = reader.readLine()) != null) {
				lineNo++;
				String line = sanitize(raw);
				if (line.isEmpty()) continue;

				int slash = line.indexOf('/');
				String ipPart = slash > 0 ? line.substring(0, slash).trim() : line;
				String prefixPart = slash > 0 ? line.substring(slash + 1).trim() : null;

				if (ipPart.indexOf(':') >= 0) {
					int prefix = prefixPart != null ? parsePrefix(prefixPart, 128) : 128;
					if (prefix < 0 || prefix > 128) continue;
					try {
						byte[] ip = InetAddress.getByName(ipPart).getAddress();
						if (ip.length == 16) {
							ipv6Ranges.add(ipv6RangeFromCidr(ip, prefix));
						}
					} catch (Exception ignored) {}
				} else {
					int prefix = prefixPart != null ? parsePrefix(prefixPart, 32) : 32;
					if (prefix < 0 || prefix > 32) continue;
					int ip = parseIpv4(ipPart);
					if (ip >= 0) {
						long[] range = ipv4RangeFromCidr(ip, prefix);
						ipv4Ranges.add(new LongRange(range[0], range[1]));
					}
				}
			}
		}
	}

	private static int parsePrefix(String str, int defaultVal) {
		try {
			return Integer.parseInt(str);
		} catch (NumberFormatException e) {
			return defaultVal;
		}
	}

	private static String sanitize(String line) {
		String t = line.trim();
		if (t.isEmpty() || t.startsWith("#") || t.startsWith("//") || t.startsWith(";"))
			return "";
		return t;
	}

	// ══════════════════════════════════════════════════════════════════════════
	// IP parsing / CIDR math
	// ══════════════════════════════════════════════════════════════════════════

	private static int parseIpv4(String ip) {
		int result = 0, octets = 0, value = 0;
		boolean hasDigit = false;

		for (int i = 0, len = ip.length(); i < len; i++) {
			char c = ip.charAt(i);
			if (c == '.') {
				if (!hasDigit || value > 255 || octets >= 3) return -1;
				result = (result << 8) | value;
				octets++; value = 0; hasDigit = false;
				continue;
			}
			if (c < '0' || c > '9') return -1;
			value = value * 10 + (c - '0');
			if (value > 255) return -1;
			hasDigit = true;
		}
		return (!hasDigit || octets != 3) ? -1 : (result << 8) | value;
	}

	private static long[] ipv4RangeFromCidr(int ip, int prefix) {
		long ipUnsigned = ip & 0xFFFFFFFFL;
		long mask  = prefix == 0 ? 0L : (0xFFFFFFFFL << (32 - prefix)) & 0xFFFFFFFFL;
		long start = ipUnsigned & mask;
		long end   = start | (~mask & 0xFFFFFFFFL);
		return new long[]{ start, end };
	}

	private static Ipv6Range ipv6RangeFromCidr(byte[] ip, int prefix) {
		long startHi = bytesToLong(ip, 0);
		long startLo = bytesToLong(ip, 8);
		long endHi, endLo;

		if (prefix == 0) {
			startHi = 0; startLo = 0; endHi = -1L; endLo = -1L;
		} else if (prefix < 64) {
			long maskHi = -1L << (64 - prefix);
			startHi &= maskHi;  startLo = 0;
			endHi = startHi | ~maskHi; endLo = -1L;
		} else if (prefix == 64) {
			startLo = 0; endHi = startHi; endLo = -1L;
		} else if (prefix < 128) {
			long maskLo = -1L << (128 - prefix);
			startLo &= maskLo;
			endHi = startHi; endLo = startLo | ~maskLo;
		} else {
			endHi = startHi; endLo = startLo;
		}

		return new Ipv6Range(startHi, startLo, endHi, endLo);
	}

	private static long bytesToLong(byte[] b, int off) {
		return ((b[off]   & 0xFFL) << 56) | ((b[off+1] & 0xFFL) << 48)
			| ((b[off+2] & 0xFFL) << 40) | ((b[off+3] & 0xFFL) << 32)
			| ((b[off+4] & 0xFFL) << 24) | ((b[off+5] & 0xFFL) << 16)
			| ((b[off+6] & 0xFFL) <<  8) |  (b[off+7] & 0xFFL);
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Range normalization
	// ══════════════════════════════════════════════════════════════════════════

	private static void normalizeIpv4Ranges(List<LongRange> ranges) {
		if (ranges.size() < 2) return;
		ranges.sort(Comparator.comparingLong(r -> r.start));

		int write = 0;
		LongRange cur = ranges.getFirst();
		for (int i = 1; i < ranges.size(); i++) {
			LongRange next = ranges.get(i);
			if (next.start <= cur.end + 1L) {
				cur = new LongRange(cur.start, Math.max(cur.end, next.end));
			} else {
				ranges.set(write++, cur);
				cur = next;
			}
		}
		ranges.set(write++, cur);
		ranges.subList(write, ranges.size()).clear();
	}

	private static void normalizeIpv6Ranges(List<Ipv6Range> ranges) {
		if (ranges.size() < 2) return;
		ranges.sort((a, b) -> {
			int c = Long.compareUnsigned(a.startHi, b.startHi);
			return c != 0 ? c : Long.compareUnsigned(a.startLo, b.startLo);
		});

		int write = 0;
		Ipv6Range cur = ranges.getFirst();
		for (int i = 1; i < ranges.size(); i++) {
			Ipv6Range next = ranges.get(i);
			if (isIpv6AdjacentOrOverlapping(cur, next)) {
				if (compareIpv6Unsigned(next.endHi, next.endLo, cur.endHi, cur.endLo) > 0)
					cur = new Ipv6Range(cur.startHi, cur.startLo, next.endHi, next.endLo);
			} else {
				ranges.set(write++, cur);
				cur = next;
			}
		}
		ranges.set(write++, cur);
		ranges.subList(write, ranges.size()).clear();
	}

	private static boolean isIpv6AdjacentOrOverlapping(Ipv6Range cur, Ipv6Range next) {
		if (compareIpv6Unsigned(next.startHi, next.startLo, cur.endHi, cur.endLo) <= 0)
			return true;
		long plusOneHi = cur.endHi;
		long plusOneLo = cur.endLo + 1;
		if (plusOneLo == 0) plusOneHi++;
		return compareIpv6Unsigned(next.startHi, next.startLo, plusOneHi, plusOneLo) <= 0;
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Lookup helpers
	// ══════════════════════════════════════════════════════════════════════════

	private static boolean isAllowedIpv4Unsigned(long ip, Snapshot s) {
		int idx = floorIndex(s.ipv4Starts, ip);
		return idx >= 0 && ip <= s.ipv4Ends[idx];
	}

	private static boolean isAllowedIpv6(byte[] ip, Snapshot s) {
		long hi = bytesToLong(ip, 0);
		long lo = bytesToLong(ip, 8);
		int idx = floorIndexIpv6(s.ipv6StartsHi, s.ipv6StartsLo, hi, lo);
		return idx >= 0 && compareIpv6Unsigned(hi, lo, s.ipv6EndsHi[idx], s.ipv6EndsLo[idx]) <= 0;
	}

	private static int floorIndex(long[] sorted, long value) {
		int low = 0, high = sorted.length - 1, result = -1;
		while (low <= high) {
			int mid = (low + high) >>> 1;
			if (sorted[mid] <= value) { result = mid; low = mid + 1; }
			else                      { high = mid - 1; }
		}
		return result;
	}

	private static int floorIndexIpv6(long[] startsHi, long[] startsLo, long hi, long lo) {
		int low = 0, high = startsHi.length - 1, result = -1;
		while (low <= high) {
			int mid = (low + high) >>> 1;
			if (compareIpv6Unsigned(startsHi[mid], startsLo[mid], hi, lo) <= 0) {
				result = mid; low = mid + 1;
			} else {
				high = mid - 1;
			}
		}
		return result;
	}

	private static int compareIpv6Unsigned(long aHi, long aLo, long bHi, long bLo) {
		int c = Long.compareUnsigned(aHi, bHi);
		return c != 0 ? c : Long.compareUnsigned(aLo, bLo);
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Address utilities
	// ══════════════════════════════════════════════════════════════════════════

	private static long ipv4ToUnsignedLong(byte[] b, int off) {
		return ((b[off] & 0xFFL) << 24) | ((b[off+1] & 0xFFL) << 16)
			| ((b[off+2] & 0xFFL) << 8) | (b[off+3] & 0xFFL);
	}

	private static boolean isIpv4MappedIpv6(byte[] b) {
		if (b.length != 16) return false;
		for (int i = 0; i < 10; i++) if (b[i] != 0) return false;
		return b[10] == (byte) 0xFF && b[11] == (byte) 0xFF;
	}

	private static boolean isAlwaysAllowed(InetAddress address) {
		return address.isLoopbackAddress() || address.isSiteLocalAddress() || address.isLinkLocalAddress() || address.isAnyLocalAddress();
	}

	private static boolean isPrivateIpv4(long ip) {
		// 127.0.0.0/8
		if ((ip & 0xFF000000L) == 0x7F000000L) return true;
		// 10.0.0.0/8
		if ((ip & 0xFF000000L) == 0x0A000000L) return true;
		// 172.16.0.0/12
		if ((ip & 0xFFF00000L) == 0xAC100000L) return true;
		// 192.168.0.0/16
		if ((ip & 0xFFFF0000L) == 0xC0A80000L) return true;
		// 169.254.0.0/16
		if ((ip & 0xFFFF0000L) == 0xA9FE0000L) return true;
		return false;
	}

	private static String benchmark(Snapshot s) {
		final int LOOPS = 100_000;
		long ipv4Sample = ipFromBytes(45, 70, 180, 1);
		long t = System.nanoTime();
		int okV4 = 0;
		for (int i = 0; i < LOOPS; i++)
			if (isAllowedIpv4Unsigned(ipv4Sample, s)) okV4++;
		long ipv4Ns = (System.nanoTime() - t) / LOOPS;

		byte[] ipv6Sample = new byte[16];
		t = System.nanoTime();
		int okV6 = 0;
		for (int i = 0; i < LOOPS; i++)
			if (isAllowedIpv6(ipv6Sample, s)) okV6++;
		long ipv6Ns = (System.nanoTime() - t) / LOOPS;

		return String.format("avg ipv4=%dns, avg ipv6=%dns", ipv4Ns, ipv6Ns);
	}

	private static long ipFromBytes(int a, int b, int c, int d) {
		return ((a & 0xFFL) << 24) | ((b & 0xFFL) << 16) | ((c & 0xFFL) << 8) | (d & 0xFFL);
	}

	// ══════════════════════════════════════════════════════════════════════════
	// Inner types
	// ══════════════════════════════════════════════════════════════════════════

	private static final class Snapshot {
		static final Snapshot DENY_ALL = new Snapshot(
			"DENY_ALL", new long[0], new long[0], new long[0], new long[0], new long[0], new long[0]);
		static final Snapshot ALLOW_ALL = new Snapshot(
			"ALLOW_ALL", new long[]{0L}, new long[]{0xFFFFFFFFL}, new long[]{0L}, new long[]{0L}, new long[]{-1L}, new long[]{-1L});

		final String sourcePath;
		final long[] ipv4Starts, ipv4Ends;
		final long[] ipv6StartsHi, ipv6StartsLo, ipv6EndsHi, ipv6EndsLo;
		final int    ipv4RangesCount, ipv6RangesCount;

		private Snapshot(String sourcePath,
			long[] ipv4Starts, long[] ipv4Ends,
			long[] ipv6StartsHi, long[] ipv6StartsLo,
			long[] ipv6EndsHi,   long[] ipv6EndsLo) {
			this.sourcePath    = sourcePath;
			this.ipv4Starts    = ipv4Starts;
			this.ipv4Ends      = ipv4Ends;
			this.ipv6StartsHi  = ipv6StartsHi;
			this.ipv6StartsLo  = ipv6StartsLo;
			this.ipv6EndsHi    = ipv6EndsHi;
			this.ipv6EndsLo    = ipv6EndsLo;
			this.ipv4RangesCount = ipv4Starts.length;
			this.ipv6RangesCount = ipv6StartsHi.length;
		}

		static Snapshot from(String sourcePath, List<LongRange> ipv4, List<Ipv6Range> ipv6) {
			int n4 = ipv4.size(), n6 = ipv6.size();
			long[] v4s = new long[n4], v4e = new long[n4];
			for (int i = 0; i < n4; i++) { v4s[i] = ipv4.get(i).start; v4e[i] = ipv4.get(i).end; }

			long[] v6sh = new long[n6], v6sl = new long[n6], v6eh = new long[n6], v6el = new long[n6];
			for (int i = 0; i < n6; i++) {
				Ipv6Range r = ipv6.get(i);
				v6sh[i] = r.startHi; v6sl[i] = r.startLo; v6eh[i] = r.endHi; v6el[i] = r.endLo;
			}
			return new Snapshot(sourcePath, v4s, v4e, v6sh, v6sl, v6eh, v6el);
		}

		static Snapshot fromArrays(String sourcePath,
			long[] ipv4Starts, long[] ipv4Ends,
			long[] ipv6StartsHi, long[] ipv6StartsLo,
			long[] ipv6EndsHi,   long[] ipv6EndsLo) {
			return new Snapshot(sourcePath, ipv4Starts, ipv4Ends, ipv6StartsHi, ipv6StartsLo, ipv6EndsHi, ipv6EndsLo);
		}
	}

	private record LongRange(long start, long end) {}

	private record Ipv6Range(long startHi, long startLo, long endHi, long endLo) {}
}
