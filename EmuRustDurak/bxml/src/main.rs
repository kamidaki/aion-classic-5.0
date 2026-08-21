use quick_xml::{
    events::{BytesEnd, BytesStart, BytesText, Event},
    writer::Writer,
};
use std::{
    collections::HashMap,
    fs::{self, File},
    io::{Read, Write},
    path::{Path, PathBuf},
};

#[macro_export]
macro_rules! consume_le_bytes {
    ($ptr:expr, $buf:expr, $ty:ty) => {{
        let size = core::mem::size_of::<$ty>();
        let ret =
            <$ty>::from_le_bytes($buf[$ptr..$ptr + size].try_into().unwrap());
        $ptr += size;
        ret
    }};
}

#[macro_export]
macro_rules! consume_varint {
    ($ptr:expr, $buf:expr) => {{
        let mut varint = 0;
        let mut i = 0;

        loop {
            let byte = consume_le_bytes!($ptr, $buf, u8);
            let remaining_bits = (byte & 0x7F) as usize;
            let shifted_bits = remaining_bits << (i * 7);
            varint ^= shifted_bits;

            i += 1;
            if (byte & 0x80) != 0x80 {
                break;
            }
        }

        varint
    }};
}

struct HeaderTable {
    /// One byte per UTF-16 LE code unit: only the low byte of each pair.
    /// The varint offsets in the bxml stream are indices into this array.
    low_bytes: Vec<u8>,
    cache: std::cell::RefCell<HashMap<usize, String>>,
}

impl HeaderTable {
    fn new(buf: &[u8]) -> Self {
        let mut low_bytes = Vec::with_capacity(buf.len() / 2 + 1);
        for bytes in buf.chunks(2) {
            low_bytes.push(bytes[0]);
        }
        Self {
            low_bytes,
            cache: std::cell::RefCell::new(HashMap::new()),
        }
    }

    fn get_string(&self, i: usize) -> String {
        if let Some(s) = self.cache.borrow().get(&i) {
            return s.clone();
        }
        let end = self.low_bytes[i..]
            .iter()
            .position(|&b| b == 0)
            .map(|p| i + p)
            .unwrap_or(self.low_bytes.len());
        let slice = &self.low_bytes[i..end];
        let s = String::from_utf8_lossy(slice).into_owned();
        self.cache.borrow_mut().insert(i, s.clone());
        s
    }
}

fn convert_one(input: &Path, output: &Path) -> Result<(), String> {
    let mut file = File::open(input)
        .map_err(|e| format!("open {}: {e}", input.display()))?;
    let mut buf = Vec::new();
    file.read_to_end(&mut buf)
        .map_err(|e| format!("read {}: {e}", input.display()))?;

    if buf.is_empty() {
        return Err(format!("{}: empty file", input.display()));
    }

    let mut len = 0;
    let magic = consume_le_bytes!(len, buf, u8);
    if magic != 0x80 {
        return Err(format!(
            "{}: wrong magic 0x{:02X} (expected 0x80)",
            input.display(),
            magic
        ));
    }

    let table_len = consume_varint!(len, buf);
    let table = HeaderTable::new(&buf[len..len + table_len]);
    len += table_len;

    let mut writer = Writer::new_with_indent(
        std::io::Cursor::new(Vec::<u8>::with_capacity(1_000_000)),
        b' ',
        2,
    );
    to_xml(&buf, &mut len, &table, &mut writer)
        .map_err(|e| format!("{}: {e}", input.display()))?;
    let xml = writer.into_inner().into_inner();

    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("mkdir {}: {e}", parent.display()))?;
    }
    let mut out = File::create(output)
        .map_err(|e| format!("create {}: {e}", output.display()))?;
    out.write_all(&xml)
        .map_err(|e| format!("write {}: {e}", output.display()))?;
    Ok(())
}

fn is_bxml(path: &Path) -> bool {
    let Ok(mut f) = File::open(path) else {
        return false;
    };
    let mut magic = [0u8; 1];
    f.read_exact(&mut magic).is_ok() && magic[0] == 0x80
}

fn walk_convert(input: &Path, output: &Path) -> (usize, usize) {
    let mut ok = 0;
    let mut err = 0;
    if input.is_file() {
        match convert_one(input, output) {
            Ok(()) => {
                ok += 1;
                println!("OK  {} -> {}", input.display(), output.display());
            }
            Err(e) => {
                err += 1;
                eprintln!("ERR {e}");
            }
        }
        return (ok, err);
    }

    let Ok(entries) = fs::read_dir(input) else {
        eprintln!("ERR: cannot read dir {}", input.display());
        return (0, 1);
    };
    for entry in entries.flatten() {
        let p = entry.path();
        let name = entry.file_name();
        let out = output.join(&name);
        if p.is_dir() {
            let (o, e) = walk_convert(&p, &out);
            ok += o;
            err += e;
        } else if p.extension().and_then(|s| s.to_str()) == Some("xml")
            && is_bxml(&p)
        {
            match convert_one(&p, &out) {
                Ok(()) => {
                    ok += 1;
                    println!("OK  {} -> {}", p.display(), out.display());
                }
                Err(e) => {
                    err += 1;
                    eprintln!("ERR {e}");
                }
            }
        }
    }
    (ok, err)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("Usage: bxml <input-file-or-dir> <output-file-or-dir>");
        eprintln!();
        eprintln!("If input is a directory, walks recursively and converts");
        eprintln!("every .xml file whose magic byte is 0x80 (binary XML).");
        std::process::exit(2);
    }

    let input = PathBuf::from(&args[1]);
    let output = PathBuf::from(&args[2]);

    let (ok, err) = walk_convert(&input, &output);
    println!("Done. {ok} converted, {err} failed.");
    if err > 0 {
        std::process::exit(1);
    }
}

fn to_xml(
    buf: &[u8],
    len: &mut usize,
    table: &HeaderTable,
    writer: &mut quick_xml::Writer<std::io::Cursor<Vec<u8>>>,
) -> Result<(), String> {
    let index = consume_varint!(*len, buf);
    let name = table.get_string(index);
    let ty = consume_varint!(*len, buf);

    writer
        .write_event(Event::Start(BytesStart::new(name.as_str())))
        .unwrap();

    match ty {
        1 => {
            let index = consume_varint!(*len, buf);
            let value = table.get_string(index);
            writer
                .write_event(Event::Text(BytesText::new(value.as_str())))
                .unwrap();
        }
        4 => {
            let count = consume_varint!(*len, buf);
            for _ in 0..count {
                to_xml(buf, len, table, writer)?;
            }
        }
        other => {
            return Err(format!(
                "unknown bxml node type {other} at node <{name}>, offset {}",
                *len
            ));
        }
    }
    writer
        .write_event(Event::End(BytesEnd::new(name.as_str())))
        .unwrap();
    Ok(())
}

