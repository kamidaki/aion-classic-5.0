use windows_sys::Win32::Foundation::{CloseHandle, HANDLE};
use windows_sys::Win32::System::JobObjects::{
    AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
    SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
};
use windows_sys::Win32::System::Threading::GetCurrentProcess;

pub struct JobObjectGuard {
    handle: HANDLE,
}

impl JobObjectGuard {
    /// Creates a Windows Job Object configured with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    /// and assigns the current process (the launcher) to it.
    /// All child processes (e.g. java.exe for ChatServer, LoginServer, GameServer)
    /// automatically inherit this job object. When the launcher terminates, crashes,
    /// or is killed via Task Manager, Windows OS automatically terminates all child processes.
    pub fn init() -> Option<Self> {
        unsafe {
            let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
            if handle == 0 {
                eprintln!("WARN: [JobObject] Failed to create Windows Job Object");
                return None;
            }

            let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

            let res = SetInformationJobObject(
                handle,
                JobObjectExtendedLimitInformation,
                &info as *const _ as *const _,
                std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
            );

            if res == 0 {
                eprintln!("WARN: [JobObject] Failed to set JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE");
                CloseHandle(handle);
                return None;
            }

            let assign_res = AssignProcessToJobObject(handle, GetCurrentProcess());
            if assign_res == 0 {
                eprintln!("WARN: [JobObject] Failed to assign current process to Job Object");
                CloseHandle(handle);
                return None;
            }

            Some(Self { handle })
        }
    }
}

impl Drop for JobObjectGuard {
    fn drop(&mut self) {
        if self.handle != 0 {
            unsafe {
                CloseHandle(self.handle);
            }
        }
    }
}
