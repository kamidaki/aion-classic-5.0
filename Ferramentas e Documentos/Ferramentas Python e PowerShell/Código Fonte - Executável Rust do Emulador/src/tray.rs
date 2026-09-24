use parking_lot::Mutex;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use windows_sys::Win32::Foundation::{HWND, LPARAM, LRESULT, POINT, WPARAM};
use windows_sys::Win32::System::LibraryLoader::GetModuleHandleW;
use windows_sys::Win32::UI::Shell::{
    Shell_NotifyIconW, NIF_ICON, NIF_MESSAGE, NIF_TIP, NIM_ADD, NIM_DELETE, NIM_MODIFY, NOTIFYICONDATAW,
};
use windows_sys::Win32::UI::WindowsAndMessaging::*;

const WM_TRAYICON: u32 = WM_USER + 100;
const ID_TRAY_OPEN: usize = 1001;
const ID_TRAY_EXIT: usize = 1002;

static IS_TRAY_REGISTERED: AtomicBool = AtomicBool::new(false);

pub struct TrayManager {
    hwnd: HWND,
    nid: NOTIFYICONDATAW,
}

unsafe impl Send for TrayManager {}
unsafe impl Sync for TrayManager {}

pub type TrayCallback = Arc<dyn Fn(TrayAction) + Send + Sync + 'static>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TrayAction {
    OpenDashboard,
    RequestShutdown,
}

static GLOBAL_CALLBACK: Mutex<Option<TrayCallback>> = Mutex::new(None);

unsafe extern "system" fn tray_wnd_proc(
    hwnd: HWND,
    msg: u32,
    wparam: WPARAM,
    lparam: LPARAM,
) -> LRESULT {
    if msg == WM_TRAYICON {
        let event = lparam as u32;
        if event == WM_LBUTTONUP || event == WM_LBUTTONDBLCLK {
            let cb_opt = GLOBAL_CALLBACK.lock().clone();
            if let Some(cb) = cb_opt {
                cb(TrayAction::OpenDashboard);
            }
            return 0;
        } else if event == WM_RBUTTONUP {
            let mut pt = POINT { x: 0, y: 0 };
            GetCursorPos(&mut pt);

            SetForegroundWindow(hwnd);
            let hmenu = CreatePopupMenu();

            let item_open: Vec<u16> = "Abrir Painel\0".encode_utf16().collect();
            let item_exit: Vec<u16> = "Encerrar Emulador\0".encode_utf16().collect();

            AppendMenuW(hmenu, MF_STRING, ID_TRAY_OPEN, item_open.as_ptr());
            AppendMenuW(hmenu, MF_SEPARATOR, 0, std::ptr::null());
            AppendMenuW(hmenu, MF_STRING, ID_TRAY_EXIT, item_exit.as_ptr());

            let selected = TrackPopupMenu(
                hmenu,
                TPM_RETURNCMD | TPM_NONOTIFY | TPM_RIGHTBUTTON,
                pt.x,
                pt.y,
                0,
                hwnd,
                std::ptr::null(),
            );

            DestroyMenu(hmenu);

            if selected == ID_TRAY_OPEN as i32 {
                let cb_opt = GLOBAL_CALLBACK.lock().clone();
                if let Some(cb) = cb_opt {
                    cb(TrayAction::OpenDashboard);
                }
            } else if selected == ID_TRAY_EXIT as i32 {
                let cb_opt = GLOBAL_CALLBACK.lock().clone();
                if let Some(cb) = cb_opt {
                    cb(TrayAction::RequestShutdown);
                }
            }
            return 0;
        }
    }
    DefWindowProcW(hwnd, msg, wparam, lparam)
}

impl TrayManager {
    pub fn init(callback: TrayCallback) -> Result<Self, &'static str> {
        unsafe {
            *GLOBAL_CALLBACK.lock() = Some(callback);

            let hinstance = GetModuleHandleW(std::ptr::null());
            let class_name: Vec<u16> = "AionClassicEmuTrayClass\0".encode_utf16().collect();
            
            let mut hicon = LoadIconW(hinstance, 1 as *const u16);
            if hicon == 0 {
                hicon = LoadIconW(0, 32512 as *const u16); // IDI_APPLICATION
            }

            let wnd_class = WNDCLASSW {
                style: 0,
                lpfnWndProc: Some(tray_wnd_proc),
                cbClsExtra: 0,
                cbWndExtra: 0,
                hInstance: hinstance,
                hIcon: hicon,
                hCursor: 0,
                hbrBackground: 0,
                lpszMenuName: std::ptr::null(),
                lpszClassName: class_name.as_ptr(),
            };

            RegisterClassW(&wnd_class);

            let hwnd = CreateWindowExW(
                0,
                class_name.as_ptr(),
                class_name.as_ptr(),
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                hinstance,
                std::ptr::null(),
            );

            if hwnd == 0 {
                return Err("Failed to create tray helper window");
            }

            let mut nid: NOTIFYICONDATAW = std::mem::zeroed();
            nid.cbSize = std::mem::size_of::<NOTIFYICONDATAW>() as u32;
            nid.hWnd = hwnd;
            nid.uID = 101;
            nid.uFlags = NIF_MESSAGE | NIF_TIP | (if hicon != 0 { NIF_ICON } else { 0 });
            nid.uCallbackMessage = WM_TRAYICON;
            nid.hIcon = hicon;

            let initial_tip = "Emulador Rust\nIniciando servidores...";
            let tip_utf16: Vec<u16> = initial_tip.encode_utf16().collect();
            let copy_len = tip_utf16.len().min(127);
            nid.szTip[..copy_len].copy_from_slice(&tip_utf16[..copy_len]);

            let res = Shell_NotifyIconW(NIM_ADD, &nid);
            if res == 0 {
                eprintln!("WARN: [Tray] Initial Shell_NotifyIconW returned 0, attempting fallback...");
            }

            IS_TRAY_REGISTERED.store(true, Ordering::SeqCst);

            Ok(Self { hwnd, nid })
        }
    }

    pub fn update_tooltip(&mut self, text: &str) {
        unsafe {
            let tip_utf16: Vec<u16> = text.encode_utf16().collect();
            let mut nid = self.nid;
            nid.uFlags = NIF_TIP;
            let copy_len = tip_utf16.len().min(127);
            nid.szTip = [0; 128];
            nid.szTip[..copy_len].copy_from_slice(&tip_utf16[..copy_len]);
            Shell_NotifyIconW(NIM_MODIFY, &nid);
        }
    }

    pub fn remove(&mut self) {
        unsafe {
            if IS_TRAY_REGISTERED.swap(false, Ordering::SeqCst) {
                Shell_NotifyIconW(NIM_DELETE, &self.nid);
            }
            if self.hwnd != 0 {
                DestroyWindow(self.hwnd);
                self.hwnd = 0;
            }
        }
    }
}

impl Drop for TrayManager {
    fn drop(&mut self) {
        self.remove();
    }
}
