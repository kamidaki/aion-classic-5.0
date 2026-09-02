use std::ffi::OsStr;
use std::os::windows::ffi::OsStrExt;
use windows_sys::Win32::Foundation::{CloseHandle, GetLastError, HANDLE, ERROR_ALREADY_EXISTS};
use windows_sys::Win32::System::Threading::CreateMutexW;
use windows_sys::Win32::UI::WindowsAndMessaging::{MessageBoxW, MB_ICONWARNING, MB_OK};

pub struct SingleInstanceGuard {
    handle: HANDLE,
}

impl SingleInstanceGuard {
    pub fn acquire(title: &str, mutex_name: &str) -> Option<Self> {
        let wide_name: Vec<u16> = OsStr::new(mutex_name)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();

        unsafe {
            let handle = CreateMutexW(std::ptr::null(), 1, wide_name.as_ptr());
            if handle == 0 {
                return None;
            }

            if GetLastError() == ERROR_ALREADY_EXISTS {
                CloseHandle(handle);

                let wide_title: Vec<u16> = OsStr::new(title)
                    .encode_wide()
                    .chain(std::iter::once(0))
                    .collect();
                let wide_msg: Vec<u16> = OsStr::new("O Aion Classic - EMU já está em execução neste computador!")
                    .encode_wide()
                    .chain(std::iter::once(0))
                    .collect();

                MessageBoxW(0, wide_msg.as_ptr(), wide_title.as_ptr(), MB_OK | MB_ICONWARNING);
                return None;
            }

            Some(Self { handle })
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
