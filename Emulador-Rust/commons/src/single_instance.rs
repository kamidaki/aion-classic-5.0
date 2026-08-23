use windows_sys::Win32::Foundation::{CloseHandle, SetLastError, ERROR_ALREADY_EXISTS, GetLastError, HANDLE};
use windows_sys::Win32::System::Threading::{CreateMutexW, ReleaseMutex};
use windows_sys::Win32::UI::WindowsAndMessaging::{MessageBoxW, MB_ICONWARNING, MB_OK, MB_SETFOREGROUND, MB_TOPMOST};

/// Guard ensuring only a single instance of a binary can execute concurrently.
pub struct SingleInstanceGuard {
    handle: HANDLE,
}

// HANDLE is isize in windows-sys 0.52
unsafe impl Send for SingleInstanceGuard {}
unsafe impl Sync for SingleInstanceGuard {}

impl SingleInstanceGuard {
    /// Attempts to acquire an exclusive named OS mutex quietly without blocking UI popups.
    pub fn acquire(app_name: &str, mutex_name: &str) -> Option<Self> {
        Self::acquire_internal(app_name, mutex_name, false)
    }

    /// Attempts to acquire an exclusive named OS mutex and displays a Windows warning MessageBox if duplicate.
    pub fn acquire_with_ui(app_name: &str, mutex_name: &str) -> Option<Self> {
        Self::acquire_internal(app_name, mutex_name, true)
    }

    fn acquire_internal(app_name: &str, mutex_name: &str, show_ui: bool) -> Option<Self> {
        unsafe {
            let wide_name: Vec<u16> = mutex_name.encode_utf16().chain(std::iter::once(0)).collect();
            let attempts = if show_ui { 1 } else { 5 };

            for attempt in 1..=attempts {
                SetLastError(0);
                let handle = CreateMutexW(std::ptr::null(), 1, wide_name.as_ptr());

                if handle == 0 {
                    eprintln!("WARN: [SingleInstance] Failed to create mutex: {}", mutex_name);
                    return None;
                }

                if GetLastError() == ERROR_ALREADY_EXISTS {
                    CloseHandle(handle);
                    if attempt < attempts {
                        std::thread::sleep(std::time::Duration::from_millis(200));
                        continue;
                    }

                    eprintln!(
                        "WARN: [SingleInstance] Este aplicativo já está em execução. Uma instância de {} já está aberta.",
                        app_name
                    );

                    if show_ui {
                        let title: Vec<u16> = "Emulador Rust\0".encode_utf16().collect();
                        let msg_text = format!(
                            "Este aplicativo já está em execução.\n\nUma instância do Emulador Rust ({}) já está aberta.",
                            app_name
                        );
                        let msg: Vec<u16> = msg_text.encode_utf16().chain(std::iter::once(0)).collect();

                        MessageBoxW(
                            0,
                            msg.as_ptr(),
                            title.as_ptr(),
                            MB_OK | MB_ICONWARNING | MB_SETFOREGROUND | MB_TOPMOST,
                        );
                    }

                    return None;
                }

                return Some(Self { handle });
            }

            None
        }
    }
}

impl Drop for SingleInstanceGuard {
    fn drop(&mut self) {
        unsafe {
            if self.handle != 0 {
                ReleaseMutex(self.handle);
                CloseHandle(self.handle);
                self.handle = 0;
            }
        }
    }
}
