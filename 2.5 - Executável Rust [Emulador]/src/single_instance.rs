use std::ffi::OsStr;
use std::os::windows::ffi::OsStrExt;
use windows_sys::Win32::Foundation::{CloseHandle, GetLastError, HANDLE, ERROR_ALREADY_EXISTS};
use windows_sys::Win32::System::Threading::CreateMutexW;
use windows_sys::Win32::UI::WindowsAndMessaging::{
    FindWindowW, MessageBoxW, SetForegroundWindow, ShowWindow, MB_ICONWARNING, MB_OK, SW_RESTORE,
};

pub struct SingleInstanceGuard {
    handle: HANDLE,
}

impl SingleInstanceGuard {
    /// Acquires a system-wide single instance mutex.
    /// If another instance of the launcher is already running, brings its window to the foreground,
    /// alerts the user, and returns None so the second process can terminate cleanly.
    /// Uses kernel Named Mutex which is automatically freed when a process terminates,
    /// avoiding false positives from dead zombie processes in the Windows process table.
    pub fn acquire(title: &str) -> Option<Self> {
        let wide_title: Vec<u16> = OsStr::new(title)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();

        // 1. Try Global Mutex first, then Local Mutex fallback
        let mutex_names = [
            "Global\\AionClassicEmu_Global_SingleInstance_Mutex",
            "Local\\AionClassicEmu_Local_SingleInstance_Mutex",
        ];

        let mut acquired_handle: Option<HANDLE> = None;
        let mut mutex_conflict = false;

        for m_name in &mutex_names {
            let wide_name: Vec<u16> = OsStr::new(m_name)
                .encode_wide()
                .chain(std::iter::once(0))
                .collect();

            unsafe {
                let handle = CreateMutexW(std::ptr::null(), 1, wide_name.as_ptr());
                if handle != 0 {
                    if GetLastError() == ERROR_ALREADY_EXISTS {
                        CloseHandle(handle);
                        mutex_conflict = true;
                        break;
                    } else if acquired_handle.is_none() {
                        acquired_handle = Some(handle);
                    }
                }
            }
        }

        if mutex_conflict {
            if let Some(h) = acquired_handle {
                unsafe { CloseHandle(h) };
            }

            unsafe {
                // Focus existing window if visible
                let hwnd = FindWindowW(std::ptr::null(), wide_title.as_ptr());
                if hwnd != 0 {
                    ShowWindow(hwnd, SW_RESTORE);
                    SetForegroundWindow(hwnd);
                }

                let wide_msg: Vec<u16> = OsStr::new("O Aion Classic - EMU já está em execução neste computador!\n\nVerifique a barra de tarefas ou a bandeja do sistema.")
                    .encode_wide()
                    .chain(std::iter::once(0))
                    .collect();

                MessageBoxW(0, wide_msg.as_ptr(), wide_title.as_ptr(), MB_OK | MB_ICONWARNING);
            }

            return None;
        }

        match acquired_handle {
            Some(handle) => Some(Self { handle }),
            None => None,
        }
    }
}

impl Drop for SingleInstanceGuard {
    fn drop(&mut self) {
        if self.handle != 0 {
            unsafe {
                CloseHandle(self.handle);
            }
        }
    }
}
