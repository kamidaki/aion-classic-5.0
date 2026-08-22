use std::{io, os::windows::raw::HANDLE, ptr::null_mut};

pub const PIPE_ACCESS_DUPLEX: u32 = 0x3;
pub const PIPE_WAIT: u32 = 0;
pub const PIPE_TYPE_BYTE: u32 = 0;
pub const PIPE_READMODE_BYTE: u32 = 0;

pub const INVALID_HANDLE_VALUE: HANDLE = usize::MAX as HANDLE;
pub const NMPWAIT_USE_DEFAULT_WAIT: u32 = 0;
pub const ERROR_BROKEN_PIPE: i32 = 109;

extern "C" {
    fn CreateNamedPipeA(
        lpName: *const u8,
        dwOpenMode: u32,
        dwPipeMode: u32,
        nMaxInstances: u32,
        nOutBufferSize: u32,
        nInBufferSize: u32,
        nDefaultTimeOut: u32,
        lpSecurityAttributes: *mut u8,
    ) -> HANDLE;
    fn ConnectNamedPipe(hNamedPipe: HANDLE, lpOverlapped: *mut u8) -> bool;
    fn ReadFile(
        hFile: HANDLE,
        lpBuffer: *mut u8,
        nNumberOfBytesToRead: u32,
        lpNumberOfBytesRead: &mut u32,
        lpOverlapped: *mut u8,
    ) -> bool;
    fn WriteFile(
        hFile: HANDLE,
        lpBuffer: *const u8,
        nNumberOfBytesToWrite: u32,
        lpNumberOfBytesWritten: &mut u32,
        lpOverlapped: *mut u8,
    ) -> bool;
    fn FlushFileBuffers(hFile: HANDLE) -> bool;
    fn DisconnectNamedPipe(hFile: HANDLE) -> bool;
    fn CloseHandle(hObject: HANDLE) -> bool;
}

#[derive(Debug)]
pub enum Error {
    CreateNamedPipeA(io::Error),
    ConnectNamedPipe(io::Error),
    ReadFile(io::Error),
    WriteFile(io::Error),
}

impl core::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl std::error::Error for Error {}

pub struct Pipe(HANDLE);

unsafe impl Send for Pipe {}
unsafe impl Sync for Pipe {}

impl Pipe {
    /// name must be null terminated
    pub fn new(name: &str, max_instances: u32) -> Result<Self, Error> {
        let pipe = unsafe {
            CreateNamedPipeA(
                name.as_ptr(),
                PIPE_ACCESS_DUPLEX,
                PIPE_WAIT | PIPE_TYPE_BYTE | PIPE_READMODE_BYTE,
                max_instances,
                0,
                0,
                NMPWAIT_USE_DEFAULT_WAIT,
                null_mut(),
            )
        };
        if pipe == INVALID_HANDLE_VALUE {
            Err(Error::CreateNamedPipeA(io::Error::last_os_error()))
        } else {
            Ok(Self(pipe))
        }
    }

    pub fn listen(&self) -> Result<(), Error> {
        let success = unsafe { ConnectNamedPipe(self.0, null_mut()) };
        if !success {
            let os_error = io::Error::last_os_error();
            if let Some(err_number) = os_error.raw_os_error() {
                if err_number == 535 {
                    return Ok(());
                }
            }
            Err(Error::ConnectNamedPipe(io::Error::last_os_error()))
        } else {
            Ok(())
        }
    }

    pub fn read(&self, buffer: &mut [u8]) -> Result<u32, Error> {
        let mut bread: u32 = 0;
        let success = unsafe {
            ReadFile(
                self.0,
                buffer.as_mut_ptr(),
                buffer.len() as u32,
                &mut bread,
                null_mut(),
            )
        };
        if !success {
            let e = io::Error::last_os_error();
            if e.raw_os_error() == Some(ERROR_BROKEN_PIPE) {
                return Ok(0);
            }
            Err(Error::ReadFile(e))
        } else {
            Ok(bread)
        }
    }

    pub fn write(&self, buffer: &[u8]) -> Result<u32, Error> {
        let mut bwritten = 0;
        let success = unsafe {
            WriteFile(
                self.0,
                buffer.as_ptr(),
                buffer.len() as u32,
                &mut bwritten,
                null_mut(),
            )
        };
        if !success {
            Err(Error::WriteFile(io::Error::last_os_error()))
        } else {
            Ok(bwritten)
        }
    }

    pub fn close(&self) -> Result<(), Error> {
        let _ = self.flush();
        let _ = self.disconnect();
        close_handle(self.0)?;
        Ok(())
    }

    fn flush(&self) -> Result<(), Error> {
        let success = unsafe { FlushFileBuffers(self.0) };
        if !success {
            Err(Error::WriteFile(io::Error::last_os_error()))
        } else {
            Ok(())
        }
    }

    fn disconnect(&self) -> Result<(), Error> {
        let success = unsafe { DisconnectNamedPipe(self.0) };
        if !success {
            Err(Error::WriteFile(io::Error::last_os_error()))
        } else {
            Ok(())
        }
    }
}

fn close_handle(handle: HANDLE) -> Result<(), Error> {
    let success = unsafe { CloseHandle(handle) };
    if !success {
        Err(Error::WriteFile(io::Error::last_os_error()))
    } else {
        Ok(())
    }
}
