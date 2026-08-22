use parking_lot::RwLock;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::broadcast;

#[derive(Debug, Clone)]
pub struct ChatMessage {
    pub sender_id: u32,
    pub sender_name: String,
    pub channel_id: u32,
    pub message: String,
}

pub struct Channel {
    pub id: u32,
    pub name: String,
    pub tx: broadcast::Sender<ChatMessage>,
}

pub struct ChannelManager {
    channels: Arc<RwLock<HashMap<u32, Arc<Channel>>>>,
    player_flood_tracker: Arc<RwLock<HashMap<u32, (Instant, u32)>>>,
    anti_flood_limit: u32,
}

impl ChannelManager {
    pub fn new(anti_flood_limit: u32) -> Self {
        let mgr = Self {
            channels: Arc::new(RwLock::new(HashMap::new())),
            player_flood_tracker: Arc::new(RwLock::new(HashMap::new())),
            anti_flood_limit,
        };

        // Create default system channels
        mgr.get_or_create_channel(1, "Global_LFG");
        mgr.get_or_create_channel(2, "Trade");
        mgr.get_or_create_channel(3, "Region_Sanctum");
        mgr.get_or_create_channel(4, "Region_Pandaemonium");

        mgr
    }

    pub fn get_or_create_channel(&self, id: u32, name: &str) -> Arc<Channel> {
        let mut map = self.channels.write();
        if let Some(ch) = map.get(&id) {
            return Arc::clone(ch);
        }

        let (tx, _) = broadcast::channel(100);
        let ch = Arc::new(Channel {
            id,
            name: name.to_string(),
            tx,
        });
        map.insert(id, Arc::clone(&ch));
        ch
    }

    pub fn subscribe(&self, channel_id: u32) -> Option<broadcast::Receiver<ChatMessage>> {
        let map = self.channels.read();
        map.get(&channel_id).map(|ch| ch.tx.subscribe())
    }

    pub fn broadcast(&self, sender_id: u32, sender_name: String, channel_id: u32, message: String) -> Result<(), &'static str> {
        // Anti-flood check
        {
            let mut tracker = self.player_flood_tracker.write();
            let now = Instant::now();
            let entry = tracker.entry(sender_id).or_insert((now, 0));
            if now.duration_since(entry.0).as_secs() >= 1 {
                entry.0 = now;
                entry.1 = 1;
            } else {
                entry.1 += 1;
                if entry.1 > self.anti_flood_limit {
                    return Err("Anti-flood limit reached. Please wait before sending another message.");
                }
            }
        }

        let map = self.channels.read();
        if let Some(ch) = map.get(&channel_id) {
            let msg = ChatMessage {
                sender_id,
                sender_name,
                channel_id,
                message,
            };
            let _ = ch.tx.send(msg);
            Ok(())
        } else {
            Err("Channel not found")
        }
    }
}
