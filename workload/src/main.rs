use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    if io::stdin().read_to_string(&mut input).is_err() {
        fail("failed to read stdin");
    }

    let value: serde_json::Value = match serde_json::from_str(&input) {
        Ok(value) => value,
        Err(_) => fail("input must be valid json"),
    };

    let response = serde_json::json!({
        "ok": true,
        "operation": "probe",
        "input": value,
    });

    let encoded = match serde_json::to_string(&response) {
        Ok(encoded) => encoded,
        Err(_) => fail("failed to encode response"),
    };

    if encoded.len() > 900 {
        fail("response exceeds 900 bytes");
    }

    let mut stdout = io::stdout();
    if stdout.write_all(encoded.as_bytes()).is_err() || stdout.flush().is_err() {
        std::process::exit(1);
    }
}

fn fail(message: &str) -> ! {
    let response = serde_json::json!({
        "ok": false,
        "error": message,
    });
    let encoded = serde_json::to_string(&response).unwrap_or_else(|_| {
        String::from("{\"ok\":false,\"error\":\"encoding failure\"}")
    });
    let _ = io::stdout().write_all(encoded.as_bytes());
    std::process::exit(1);
}
