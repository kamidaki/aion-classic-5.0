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
    /// Attempts to acquire an exclusive named OS mutex.
    /// If another instance already holds the mutex, shows a warning MessageBox,
    /// logs the event, and returns None.
    pub fn acquire(app_name: &str, mutex_name: &str) -> Option<Self> {
        unsafe {
            SetLastError(0);
            let wide_name: Vec<u16> = mutex_name.encode_utf16().chain(std::iter::once(0)).collect();
            let handle = CreateMutexW(std::ptr::null(), 1, wide_name.as_ptr());

            if handle == 0 {
                eprintln!("WARN: [SingleInstance] Failed to create mutex: {}", mutex_name);
                return None;
            }

            if GetLastError() == ERROR_ALREADY_EXISTS {
                eprintln!(
                    "WARN: [SingleInstance] Este aplicativo já está em execução. Uma instância de {} já está aberta.",
                    app_name
                );

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

                CloseHandle(handle);
                return None;
            }

            Some(Self { handle })
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
