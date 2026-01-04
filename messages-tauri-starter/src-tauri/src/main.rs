#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::PathBuf;

#[tauri::command]
fn ensure_backup_dir() -> Result<String, String> {
  // Prefer system-wide Application Support (/Library/Application Support/...)
  let system_base: PathBuf = PathBuf::from("/")
    .join("Library")
    .join("Application Support")
    .join("iMessageWrapped");

  if let Ok(_) = std::fs::create_dir_all(&system_base) {
    let backups = system_base.join("backups");
    std::fs::create_dir_all(&backups).map_err(|e| e.to_string())?;
    return Ok(backups.to_string_lossy().to_string());
  }

  // Fallback to per-user Application Support
  let home = std::env::var("HOME").map_err(|e| e.to_string())?;
  let user_base: PathBuf = PathBuf::from(home)
    .join("Library")
    .join("Application Support")
    .join("iMessageWrapped");

  std::fs::create_dir_all(&user_base).map_err(|e| e.to_string())?;
  let backups = user_base.join("backups");
  std::fs::create_dir_all(&backups).map_err(|e| e.to_string())?;
  Ok(backups.to_string_lossy().to_string())
}

#[tauri::command]
fn normalize_path(path: String) -> Result<String, String> {
  let p = PathBuf::from(path);
  match std::fs::metadata(&p) {
    Ok(md) => {
      if md.is_dir() {
        Ok(p.to_string_lossy().to_string())
      } else {
        match p.parent() {
          Some(parent) => Ok(parent.to_string_lossy().to_string()),
          None => Ok(p.to_string_lossy().to_string()),
        }
      }
    }
    Err(_) => {
      // if metadata fails, try to use parent as a fallback
      match p.parent() {
        Some(parent) => Ok(parent.to_string_lossy().to_string()),
        None => Ok(p.to_string_lossy().to_string()),
      }
    }
  }
}

use serde_json::Value;

#[tauri::command]
fn run_backend(payload: Value) -> Result<String, String> {
  // Accept either `exports_dir` (snake_case) or `exportsDir` (camelCase)
  let exports_dir = payload
    .get("exports_dir")
    .and_then(|v: &Value| v.as_str())
    .map(|s| s.to_string())
    .or_else(|| payload.get("exportsDir").and_then(|v: &Value| v.as_str()).map(|s| s.to_string()));

  if let Some(ed) = exports_dir {
    run_backend_internal(&ed)
  } else {
    Err("Missing required parameter `exports_dir` or `exportsDir`".to_string())
  }
}

// Core backend runner used by both the Tauri command and the local HTTP server
fn run_backend_internal(exports_dir: &str) -> Result<String, String> {
  use std::process::Command;
  // Try packaged binary first (relative to project root src-tauri/binaries)
  let cwd = std::env::current_dir().map_err(|e| e.to_string())?;
  let mut bin_path = cwd.join("src-tauri").join("binaries").join("MessagesWrapped");
  if !bin_path.exists() {
    // try without src-tauri (in case current_dir is src-tauri)
    bin_path = cwd.join("binaries").join("MessagesWrapped");
  }

  let args = [format!("--exports-dir={}", exports_dir), String::from("--max-workers=4")];

  if bin_path.exists() {
    match Command::new(bin_path).args(&args).output() {
      Ok(out) => {
        let mut combined = String::new();
        combined.push_str(&String::from_utf8_lossy(&out.stdout));
        combined.push_str(&String::from_utf8_lossy(&out.stderr));
        if out.status.success() {
          Ok(combined)
        } else {
          Err(combined)
        }
      }
      Err(e) => Err(format!("Failed to execute binary: {}", e)),
    }
  } else {
    // Fallback to running the python script from the Backend folder
    // Try ../Backend/MessagesWrapped.py and Backend/MessagesWrapped.py
    let mut script_path = cwd.join("../Backend/MessagesWrapped.py");
    if !script_path.exists() {
      script_path = cwd.join("Backend").join("MessagesWrapped.py");
    }
    if !script_path.exists() {
      return Err(format!("No backend binary or script found. Checked {}", script_path.display()));
    }

    match Command::new("python3").arg(script_path).args(&args).output() {
      Ok(out) => {
        let mut combined = String::new();
        combined.push_str(&String::from_utf8_lossy(&out.stdout));
        combined.push_str(&String::from_utf8_lossy(&out.stderr));
        if out.status.success() {
          Ok(combined)
        } else {
          Err(combined)
        }
      }
      Err(e) => Err(format!("Failed to spawn python3: {}", e)),
    }
  }
}

// Spawn a tiny local HTTP server on 127.0.0.1:39213 to accept /run?exports_dir=...
fn spawn_local_runner() {
  use std::io::{Read, Write};
  use std::net::TcpListener;
  use std::thread;

  thread::spawn(|| {
    let listener = match TcpListener::bind(("127.0.0.1", 39213)) {
      Ok(l) => l,
      Err(_) => return,
    };
    for stream in listener.incoming() {
      if let Ok(mut s) = stream {
        let mut buf = [0u8; 8192];
        if let Ok(n) = s.read(&mut buf) {
          if n == 0 { continue; }
          let req = String::from_utf8_lossy(&buf[..n]).to_string();
          let first_line = req.lines().next().unwrap_or("");
          let parts: Vec<&str> = first_line.split_whitespace().collect();
          if parts.len() >= 2 {
            let path = parts[1];
            if path.starts_with("/run") {
              // parse query string
              let exports_dir = if let Some(qi) = path.find('?') {
                let qs = &path[qi+1..];
                // find exports_dir param
                let mut val = "".to_string();
                for p in qs.split('&') {
                  if p.starts_with("exports_dir=") {
                    val = p[13..].to_string();
                    break;
                  }
                }
                // percent-decode
                simple_percent_decode(&val)
              } else { String::new() };

              let response = match run_backend_internal(&exports_dir) {
                Ok(out) => format!("OK\n{}", out),
                Err(e) => format!("ERROR\n{}", e),
              };
              let body = response;
              let resp = format!("HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: {}\r\n\r\n{}", body.len(), body);
              let _ = s.write_all(resp.as_bytes());
              let _ = s.flush();
            } else {
              let body = "Not Found";
              let resp = format!("HTTP/1.1 404 Not Found\r\nContent-Length: {}\r\n\r\n{}", body.len(), body);
              let _ = s.write_all(resp.as_bytes());
            }
          }
        }
      }
    }
  });
}

// simple percent-decode for query param values
fn simple_percent_decode(input: &str) -> String {
  let mut out = String::with_capacity(input.len());
  let mut chars = input.chars();
  while let Some(c) = chars.next() {
    if c == '%' {
      let hi = chars.next().unwrap_or('0');
      let lo = chars.next().unwrap_or('0');
      if let (Some(hi_v), Some(lo_v)) = (hi.to_digit(16), lo.to_digit(16)) {
        let byte = (hi_v * 16 + lo_v) as u8;
        out.push(byte as char);
      } else {
        out.push(c);
        out.push(hi);
        out.push(lo);
      }
    } else if c == '+' {
      out.push(' ');
    } else {
      out.push(c);
    }
  }
  out
}

fn main() {
  // start local HTTP runner (used as a fallback to run backend without relying on Tauri invoke/allowlist)
  spawn_local_runner();

  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![ensure_backup_dir, normalize_path, run_backend])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
