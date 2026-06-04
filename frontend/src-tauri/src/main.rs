// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::Mutex;

struct BackendProcess(Mutex<Option<Child>>);

/// Launch the Python backend as a sidecar subprocess.
fn launch_backend() -> Option<Child> {
    let python = if cfg!(target_os = "windows") {
        "python"
    } else {
        "python3"
    };

    match Command::new(python)
        .args(["-m", "cinematic_mood_weaver.main"])
        .current_dir("../backend")
        .spawn()
    {
        Ok(child) => {
            println!("[Tauri] Backend launched with PID {}", child.id());
            Some(child)
        }
        Err(e) => {
            eprintln!("[Tauri] Failed to launch backend: {}", e);
            None
        }
    }
}

fn main() {
    let backend = launch_backend();

    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(backend)))
        .on_window_event(|event| {
            if let tauri::WindowEvent::Destroyed = event.event() {
                // Kill the backend when the window closes
                if let Some(state) = event.window().try_state::<BackendProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            let _ = child.kill();
                            let _ = child.wait();
                            println!("[Tauri] Backend process terminated");
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
