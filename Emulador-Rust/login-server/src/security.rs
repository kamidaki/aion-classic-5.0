use parking_lot::Mutex;
use std::collections::HashMap;
use std::net::IpAddr;
use std::sync::Arc;
use std::time::{Duration, Instant};

#[derive(Clone)]
pub struct SecurityManager {
    rate_limiter: Arc<Mutex<HashMap<IpAddr, (Instant, u32)>>>,
    banned_ips: Arc<Mutex<HashMap<IpAddr, Instant>>>,
    max_attempts: u32,
    ban_duration: Duration,
    enabled: bool,
}

impl SecurityManager {
    pub fn new(enabled: bool, max_attempts: u32, ban_minutes: u32) -> Self {
        Self {
            rate_limiter: Arc::new(Mutex::new(HashMap::new())),
            banned_ips: Arc::new(Mutex::new(HashMap::new())),
            max_attempts,
            ban_duration: Duration::from_secs(ban_minutes as u64 * 60),
            enabled,
        }
    }

    pub fn check_connection(&self, ip: IpAddr) -> bool {
        if !self.enabled {
            return true;
        }

        let now = Instant::now();

        // Check if currently banned
        {
            let mut banned = self.banned_ips.lock();
            if let Some(&ban_time) = banned.get(&ip) {
                if now.duration_since(ban_time) < self.ban_duration {
                    return false;
                } else {
                    banned.remove(&ip);
                }
            }
        }

        // Check rate limiter
        {
            let mut limits = self.rate_limiter.lock();
            let entry = limits.entry(ip).or_insert((now, 0));
            if now.duration_since(entry.0).as_secs() >= 60 {
                entry.0 = now;
                entry.1 = 1;
            } else {
                entry.1 += 1;
                if entry.1 > self.max_attempts {
                    // Trigger temporary ban
                    let mut banned = self.banned_ips.lock();
                    banned.insert(ip, now);
                    println!("WARN: [LoginSecurity] IP {} exceeded {} attempts/min and is temporarily banned for {:?}.", ip, self.max_attempts, self.ban_duration);
                    return false;
                }
            }
        }

        true
    }

    pub fn sanitize_username(name: &str) -> String {
        name.chars()
            .filter(|c| c.is_alphanumeric() || *c == '_' || *c == '-' || *c == '.')
            .take(32)
            .collect()
    }
}
