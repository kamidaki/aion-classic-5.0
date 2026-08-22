mod db;
mod error;
mod net;

use std::net::{TcpListener, TcpStream};
use std::sync::Arc;
use std::thread::spawn;
use std::time::Duration;

use crate::db::Db;
use crate::error::Error;
use crate::net::Session;

const DB_PATH: &str = "aion.db";

fn main() {
    println!("INFO: Starting STS Server");
    let db = Arc::new(Db::open(DB_PATH).expect("failed to open STS db"));
    println!("INFO: Opened shared DB at {DB_PATH}");

    let listener = TcpListener::bind("0.0.0.0:6600").unwrap();
    println!("INFO: Listening on {}", listener.local_addr().unwrap());

    while let Ok((stream, _)) = listener.accept() {
        let db = db.clone();
        spawn(move || {
            if let Err(e) = handle(stream, db) {
                eprintln!("ERROR: session failed: {e:?}");
            }
        });
    }
}

fn handle(stream: TcpStream, db: Arc<Db>) -> error::Result<()> {
    println!(
        "INFO: new session {}",
        stream.peer_addr().map_err(Error::PeerAddr)?
    );

    stream
        .set_read_timeout(Some(Duration::from_secs(60)))
        .map_err(Error::SetStreamTimeout)?;
    stream
        .set_write_timeout(Some(Duration::from_secs(60)))
        .map_err(Error::SetStreamTimeout)?;

    Session::new(db).handle(stream)
}
