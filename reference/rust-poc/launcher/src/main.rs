mod auth;
mod gameforge;

use std::io::{BufRead, BufWriter, ErrorKind, Write};
use std::process::Command;
use std::sync::{Arc, Mutex};

// ---------------------------------------------------------------------------
// Config — adjust these to match your installation
// ---------------------------------------------------------------------------

const GAME_PATH: &str = r#"G:\GFAion\aionclassic\bin64\aion.bin"#;
const AUTH_SERVER: &str = "127.0.0.1";
const STS_SERVER: &str = "127.0.0.1";
const DEFAULT_DEV_USERNAME: &str = "dev";

// ---------------------------------------------------------------------------
// Shared launcher state
// ---------------------------------------------------------------------------

/// State shared between the UI thread and the named-pipe RPC server thread.
pub struct LauncherState {
    /// The logged-in username. Empty when not logged in.
    /// Returned as the auth code to the Aion client; the STS server uses it
    /// as the account identifier when issuing a game session token.
    pub username: String,
}

impl LauncherState {
    fn new() -> Self {
        Self {
            username: String::new(),
        }
    }

    fn is_logged_in(&self) -> bool {
        !self.username.is_empty()
    }
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

fn prompt_login(state: &Arc<Mutex<LauncherState>>) {
    let stdin = std::io::stdin();
    let mut w = BufWriter::new(std::io::stdout());

    write!(w, "Username: ").unwrap();
    w.flush().unwrap();

    let mut input = String::new();
    stdin.lock().read_line(&mut input).unwrap();
    let username = input.trim().to_string();

    if username.is_empty() {
        println!("WARN: empty username, try again.");
        return;
    }

    state.lock().unwrap().username = username.clone();
    println!("INFO: logged in as '{username}'");
}

fn launch_game(state: &Arc<Mutex<LauncherState>>) {
    let username = {
        let s = state.lock().unwrap();
        if !s.is_logged_in() {
            println!("ERROR: not logged in — choose option 1 first.");
            return;
        }
        s.username.clone()
    };

    println!("INFO: launching game as '{username}'");
    println!("INFO:   auth-server  → {AUTH_SERVER}:13001");
    println!("INFO:   STS server   → {STS_SERVER}:6600");
    println!("INFO:   game binary  → {GAME_PATH}");

    let result = Command::new(GAME_PATH)
        // Disable the in-game cash shop / premium server calls
        .arg("-dnpshop")
        // Display language
        .arg("-lang:ENG")
        // Use the Gameforge / HQ auth path so the client connects through
        // our auth-server on port 13001 and then to STS on 6600.
        .env("_TNT_SESSION_ID", "")
        .env("_TNT_CLIENT_APPLICATION_ID", "")
        .arg(format!("-ip:{AUTH_SERVER}"))
        .arg("-port:2106")
        .arg("-usehqserver")
        .arg(format!("-hqip:{AUTH_SERVER}"))
        .arg("-hqport:13001")
        .arg(format!("-np:{STS_SERVER}"))
        .arg("-dwsm")
        .arg("-pwd16")
        .arg("-npsa")
        .arg("-probability")
        .arg("-nospamcheck")
        .arg("-noweb")
        .arg("-nowebshop")
        .arg("-st")
        .arg("-dpetition")
        .arg("-hidepromo")
        .arg("-nosatab")
        .arg("-nosarefund")
        .arg("-dingameshop")
        .arg("-disabletempbanner")
        .arg("-disabledevaschedule")
        .arg("-recserveridx:1")
        .arg("-old_charInstance")
        .stdout(std::process::Stdio::inherit())
        .stderr(std::process::Stdio::inherit())
        .spawn();

    match result {
        Err(ref e) if e.kind() == ErrorKind::NotFound => {
            eprintln!("ERROR: game binary not found at '{GAME_PATH}'");
            eprintln!("       Update GAME_PATH in launcher/src/main.rs");
        }
        Err(e) => eprintln!("ERROR: failed to spawn game process: {e}"),
        Ok(_) => println!("INFO: game process spawned — launcher stays open"),
    }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

fn main() {
    println!("INFO: Aion private-server launcher");
    println!("INFO: pipe RPC server starting in background...");

    let state = Arc::new(Mutex::new(LauncherState::new()));

    // The named-pipe thread impersonates the GameForge client so the Aion
    // binary can call ClientLibrary.* RPCs as usual.
    let pipe_state = Arc::clone(&state);
    std::thread::spawn(|| gameforge::listen(pipe_state));

    let args = std::env::args().skip(1).collect::<Vec<_>>();
    if args.first().map(String::as_str) == Some("--auto") {
        let username = args
            .get(1)
            .cloned()
            .unwrap_or_else(|| DEFAULT_DEV_USERNAME.to_string());
        state.lock().unwrap().username = username.clone();
        println!("INFO: auto-login enabled as '{username}'");
        launch_game(&state);

        loop {
            std::thread::sleep(std::time::Duration::from_secs(60));
        }
    }

    let stdin = std::io::stdin();
    let mut w = BufWriter::new(std::io::stdout());

    loop {
        let (logged_in, username) = {
            let s = state.lock().unwrap();
            (s.is_logged_in(), s.username.clone())
        };

        writeln!(w).unwrap();
        writeln!(w, "1. Login").unwrap();
        if logged_in {
            writeln!(w, "2. Launch game  [logged in as '{username}']").unwrap();
        } else {
            writeln!(w, "2. Launch game  [not logged in]").unwrap();
        }
        writeln!(w, "3. Exit").unwrap();
        write!(w, "> ").unwrap();
        w.flush().unwrap();

        let mut input = String::new();
        stdin.lock().read_line(&mut input).unwrap();

        match input.trim() {
            "1" => prompt_login(&state),
            "2" => launch_game(&state),
            "3" => break,
            other => println!("Unknown option '{other}', try again."),
        }
    }
}
