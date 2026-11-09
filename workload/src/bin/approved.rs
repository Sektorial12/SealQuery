use std::io::{self, Read, Write};

use outlayer::storage;
use sealquery_workload::{
    compute_spend_growth, upload_dataset_meta, validate_version, SpendGrowthParams,
};
use serde_json::{json, Value};

fn main() {
    let mut input = String::new();
    if io::stdin().read_to_string(&mut input).is_err() {
        fail("failed to read stdin");
    }

    let request: Value = match serde_json::from_str(&input) {
        Ok(value) => value,
        Err(_) => fail("input must be valid json"),
    };

    let operation = request
        .get("operation")
        .and_then(Value::as_str)
        .unwrap_or("");

    let response = match operation {
        "probe" => json!({
            "ok": true,
            "operation": "probe",
            "input": request,
        }),
        "upload_dataset" => {
            require_secret("PROTECTED_DATASET_UPLOAD_TOKEN");
            let version = request.get("version").and_then(Value::as_str).unwrap_or("");
            if let Err(error) = validate_version(version) {
                fail(&error);
            }
            let dataset = request
                .get("dataset_csv")
                .and_then(Value::as_str)
                .unwrap_or("");
            let expected = request
                .get("expected_sha256")
                .and_then(Value::as_str)
                .unwrap_or("");
            if dataset.is_empty() {
                fail("dataset_csv is required");
            }
            let mut metadata = match upload_dataset_meta(version, dataset.as_bytes(), expected) {
                Ok(value) => value,
                Err(error) => fail(&error),
            };
            let key = format!("dataset:{version}");
            if let Err(error) = storage::set_worker(&key, dataset.as_bytes()) {
                fail(&format!("failed to store dataset: {error}"));
            }
            metadata["stored"] = Value::Bool(true);
            metadata
        }
        "spend_growth" => {
            require_secret("PROTECTED_COMPUTE_ACCESS_TOKEN");
            let params: SpendGrowthParams = match serde_json::from_value(request) {
                Ok(params) => params,
                Err(error) => fail(&format!("invalid spend_growth params: {error}")),
            };
            let key = format!("dataset:{}", params.version);
            let dataset = match storage::get_worker(&key) {
                Ok(Some(bytes)) => bytes,
                Ok(None) => fail("dataset not found"),
                Err(error) => fail(&format!("failed to read dataset: {error}")),
            };
            let dataset = match String::from_utf8(dataset) {
                Ok(text) => text,
                Err(_) => fail("dataset is not valid utf-8"),
            };
            match compute_spend_growth(&dataset, &params) {
                Ok(value) => value,
                Err(error) => fail(&error),
            }
        }
        _ => fail("unknown operation"),
    };

    respond(&response);
}

fn require_secret(name: &str) {
    match std::env::var(name) {
        Ok(value) if !value.is_empty() => {}
        _ => fail(&format!("missing required secret: {name}")),
    }
}

fn respond(value: &Value) {
    let encoded = match serde_json::to_string(value) {
        Ok(encoded) => encoded,
        Err(_) => fail("failed to encode response"),
    };
    if encoded.len() > 900 {
        fail("response exceeds 900 bytes");
    }
    write_stdout(&encoded);
}

fn fail(message: &str) -> ! {
    let response = json!({
        "ok": false,
        "error": message,
    });
    let encoded = serde_json::to_string(&response)
        .unwrap_or_else(|_| String::from("{\"ok\":false,\"error\":\"encoding failure\"}"));
    write_stdout(&encoded);
    std::process::exit(1);
}

fn write_stdout(value: &str) {
    let mut stdout = io::stdout();
    let _ = stdout.write_all(value.as_bytes());
    let _ = stdout.flush();
}
