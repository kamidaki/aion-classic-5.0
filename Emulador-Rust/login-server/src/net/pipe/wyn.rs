use std::ffi::c_void;
use std::io;
use std::ptr::null_mut;

type Handle = *mut c_void;

#[link(name = "kernel32")]
extern "system" {
    fn CreateNamedPipeA(
        lpName: *const u8,
        dwOpenMode: u32,
        dwPipeMode: u32,
        nMaxInstances: u32,
        nOutBufferSize: u32,
        nInBufferSize: u32,
        nDefaultTimeOut: u32,
        lpSecurityAttributes: *mut c_void,
    ) -> Handle;

    fn ConnectNamedPipe(hNamedPipe: Handle, lpOverlapped: *mut c_void) -> i32;
    fn ReadFile(
        hFile: Handle,
        lpBuffer: *mut u8,
        nNumberOfBytesToRead: u32,
        lpNumberOfBytesRead: *mut u32,
        lpOverlapped: *mut c_void,
    ) -> i32;

    fn WriteFile(
        hFile: Handle,
        lpBuffer: *const u8,
        nNumberOfBytesToWrite: u32,
        lpNumberOfBytesWritten: *mut u32,
        lpOverlapped: *mut c_void,
    ) -> i32;

    fn DisconnectNamedPipe(hNamedPipe: Handle) -> i32;
    fn CloseHandle(hObject: Handle) -> i32;
}

#[derive(Debug)]
pub enum PipeError {
    CreateNamedPipeA,
    ConnectNamedPipe,
    ReadFile,
    WriteFile,
}

pub struct NamedPipe(Handle);

impl NamedPipe {
    pub fn create(name: &str) -> Result<Self, PipeError> {
        let mut null_terminated = name.to_string();
        null_terminated.push('\0');

        let handle = unsafe {
            CreateNamedPipeA(
                null_terminated.as_ptr(),
                0x00000003, // PIPE_ACCESS_DUPLEX
                0x00000000, // PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT
                255,        // PIPE_UNLIMITED_INSTANCES
                4096,
                4096,
                0,
                null_mut(),
            )
        };

        if handle == null_mut() || handle == -1isize as Handle {
            Err(PipeError::CreateNamedPipeA)
        } else {
            Ok(Self(handle))
        }
    }

    pub fn accept(&self) -> Result<(), PipeError> {
        let res = unsafe { ConnectNamedPipe(self.0, null_mut()) };
        if res == 0 {
            let err = io::Error::last_os_error();
            if err.raw_os_error() == Some(535) {
                // ERROR_PIPE_CONNECTED
                Ok(())
            } else {
                Err(PipeError::ConnectNamedPipe)
            }
        } else {
            Ok(())
        }
    }

    pub fn read(&self, buf: &mut [u8]) -> Result<usize, PipeError> {
        let mut read = 0u32;
        let res = unsafe {
            ReadFile(
                self.0,
                buf.as_mut_ptr(),
                buf.len() as u32,
                &mut read,
                null_mut(),
            )
        };
        if res == 0 {
            Err(PipeError::ReadFile)
        } else {
            Ok(read as usize)
        }
    }

    pub fn write_all(&self, buf: &[u8]) -> Result<(), PipeError> {
        let mut written = 0u32;
        let res = unsafe {
            WriteFile(
                self.0,
                buf.as_ptr(),
                buf.len() as u32,
                &mut written,
                null_mut(),
            )
        };
        if res == 0 {
            Err(PipeError::WriteFile)
        } else {
            Ok(())
        }
    }

    pub fn disconnect(&self) {
        unsafe {
            DisconnectNamedPipe(self.0);
        }
    }
}

impl Drop for NamedPipe {
    fn drop(&mut self) {
        unsafe {
            CloseHandle(self.0);
        }
    }
}
