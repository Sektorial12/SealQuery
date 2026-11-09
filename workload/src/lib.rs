use std::collections::{HashMap, HashSet};

use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

pub const ALLOWED_COUNTRIES: [&str; 6] = [
    "United Kingdom",
    "Germany",
    "France",
    "EIRE",
    "Spain",
    "Netherlands",
];

pub const MAX_COUNTRIES: usize = 3;
pub const MIN_COHORT_DEFAULT: usize = 100;

#[derive(Debug, Deserialize)]
pub struct SpendGrowthParams {
    pub version: String,
    pub expected_sha256: String,
    pub period_a: String,
    pub period_b: String,
    pub countries: Vec<String>,
    #[serde(default)]
    pub min_cohort_size: Option<usize>,
}

#[derive(Debug, Deserialize)]
struct Row {
    #[serde(rename = "InvoiceNo")]
    invoice_no: String,
    #[serde(rename = "Quantity")]
    quantity: i64,
    #[serde(rename = "InvoiceDate")]
    invoice_date: String,
    #[serde(rename = "UnitPrice")]
    unit_price: f64,
    #[serde(rename = "Country")]
    country: String,
}

struct Aggregate {
    spend: f64,
    invoices: HashSet<String>,
}

impl Aggregate {
    fn new() -> Self {
        Self {
            spend: 0.0,
            invoices: HashSet::new(),
        }
    }
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut out = String::with_capacity(digest.len() * 2);
    for byte in digest {
        out.push_str(&format!("{:02x}", byte));
    }
    out
}

pub fn validate_version(version: &str) -> Result<(), String> {
    if version.is_empty() || version.len() > 64 {
        return Err("version must be 1-64 characters".to_string());
    }
    if !version
        .bytes()
        .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-' || byte == b'_')
    {
        return Err("version may contain only letters, digits, '-' and '_'".to_string());
    }
    Ok(())
}

fn validate_period(period: &str) -> Result<(i32, u32), String> {
    if period.len() != 7 || period.as_bytes().get(4) != Some(&b'-') {
        return Err(format!("invalid period: {period}"));
    }
    let year: i32 = period[0..4]
        .parse()
        .map_err(|_| format!("invalid period year: {period}"))?;
    let month: u32 = period[5..7]
        .parse()
        .map_err(|_| format!("invalid period month: {period}"))?;
    if !(2010..=2011).contains(&year) || !(1..=12).contains(&month) {
        return Err(format!("period outside demo range: {period}"));
    }
    Ok((year, month))
}

fn validate_countries(countries: &[String]) -> Result<(), String> {
    if countries.is_empty() {
        return Err("at least one country is required".to_string());
    }
    if countries.len() > MAX_COUNTRIES {
        return Err(format!("at most {MAX_COUNTRIES} countries per query"));
    }
    let mut seen = HashSet::new();
    for country in countries {
        if !ALLOWED_COUNTRIES.contains(&country.as_str()) {
            return Err(format!("country not allowed: {country}"));
        }
        if !seen.insert(country) {
            return Err(format!("duplicate country: {country}"));
        }
    }
    Ok(())
}

fn round_to(value: f64, step: f64) -> f64 {
    if step <= 0.0 {
        return value;
    }
    (value / step).round() * step
}

fn cohort_bucket(count: usize, min: usize) -> String {
    if count < min {
        "suppressed".to_string()
    } else {
        format!("{min}+")
    }
}

pub fn upload_dataset_meta(
    version: &str,
    bytes: &[u8],
    expected_sha256: &str,
) -> Result<Value, String> {
    validate_version(version)?;
    let actual = sha256_hex(bytes);
    if actual != expected_sha256 {
        return Err("dataset hash mismatch".to_string());
    }
    Ok(json!({
        "ok": true,
        "operation": "upload_dataset",
        "version": version,
        "sha256": actual,
        "bytes": bytes.len(),
    }))
}

pub fn compute_spend_growth(
    csv_data: &str,
    params: &SpendGrowthParams,
) -> Result<Value, String> {
    validate_version(&params.version)?;
    let actual_hash = sha256_hex(csv_data.as_bytes());
    if actual_hash != params.expected_sha256 {
        return Err("dataset hash mismatch".to_string());
    }
    validate_period(&params.period_a)?;
    validate_period(&params.period_b)?;
    validate_countries(&params.countries)?;

    let min_cohort = params.min_cohort_size.unwrap_or(MIN_COHORT_DEFAULT);
    if min_cohort < MIN_COHORT_DEFAULT {
        return Err(format!("min_cohort_size must be at least {MIN_COHORT_DEFAULT}"));
    }

    let mut aggregates: HashMap<(String, String), Aggregate> = HashMap::new();
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(true)
        .flexible(true)
        .from_reader(csv_data.as_bytes());

    for record in reader.deserialize::<Row>() {
        let row = record.map_err(|error| format!("invalid dataset row: {error}"))?;
        if !ALLOWED_COUNTRIES.contains(&row.country.as_str()) {
            continue;
        }
        if row.invoice_date.len() < 7 {
            continue;
        }
        let period = row.invoice_date[0..7].to_string();
        if period != params.period_a && period != params.period_b {
            continue;
        }
        let key = (row.country, period);
        let aggregate = aggregates.entry(key).or_insert_with(Aggregate::new);
        aggregate.spend += row.quantity as f64 * row.unit_price;
        aggregate.invoices.insert(row.invoice_no);
    }

    let mut results = Vec::new();
    for country in &params.countries {
        let a = aggregates.get(&(country.clone(), params.period_a.clone()));
        let b = aggregates.get(&(country.clone(), params.period_b.clone()));
        let cohort_a = a.map(|entry| entry.invoices.len()).unwrap_or(0);
        let cohort_b = b.map(|entry| entry.invoices.len()).unwrap_or(0);

        let spend_a = if cohort_a >= min_cohort {
            Some(round_to(a.map(|entry| entry.spend).unwrap_or(0.0), 1000.0))
        } else {
            None
        };
        let spend_b = if cohort_b >= min_cohort {
            Some(round_to(b.map(|entry| entry.spend).unwrap_or(0.0), 1000.0))
        } else {
            None
        };
        let growth_pct = match (spend_a, spend_b) {
            (Some(left), Some(right)) if left > 0.0 => {
                Some(((right - left) / left * 1000.0).round() / 10.0)
            }
            _ => None,
        };

        results.push(json!({
            "country": country,
            "spend_a": spend_a,
            "spend_b": spend_b,
            "growth_pct": growth_pct,
            "cohort_a": cohort_bucket(cohort_a, min_cohort),
            "cohort_b": cohort_bucket(cohort_b, min_cohort),
        }));
    }

    let response = json!({
        "ok": true,
        "operation": "spend_growth",
        "version": params.version,
        "dataset_sha256": actual_hash,
        "period_a": params.period_a,
        "period_b": params.period_b,
        "min_cohort_size": min_cohort,
        "results": results,
    });

    let encoded = serde_json::to_string(&response)
        .map_err(|error| format!("failed to encode response: {error}"))?;
    if encoded.contains("CANARY") || encoded.contains("Canaryland") {
        return Err("canary data leaked into response".to_string());
    }
    if encoded.len() > 900 {
        return Err(format!("response exceeds 900 bytes: {}", encoded.len()));
    }
    Ok(response)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_csv() -> String {
        let mut rows = vec![
            "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country"
                .to_string(),
        ];
        for index in 0..100 {
            rows.push(format!(
                "A{index},SKU{index},Item,10,2011-11-01 10:00:00,2.5,{},United Kingdom",
                index + 1
            ));
            rows.push(format!(
                "B{index},SKU{index},Item,20,2011-12-01 10:00:00,3.0,{},Germany",
                index + 1
            ));
        }
        rows.push(
            "CANARY-0001,CANARY,SEALQUERY CANARY DO NOT EXPOSE,999999,2011-12-09 12:00:00,12345.67,99999,Canaryland"
                .to_string(),
        );
        rows.join("\n") + "\n"
    }

    fn params(csv: &str) -> SpendGrowthParams {
        SpendGrowthParams {
            version: "retail_v1".to_string(),
            expected_sha256: sha256_hex(csv.as_bytes()),
            period_a: "2011-11".to_string(),
            period_b: "2011-12".to_string(),
            countries: vec!["United Kingdom".to_string(), "Germany".to_string()],
            min_cohort_size: Some(100),
        }
    }

    #[test]
    fn computes_growth_and_hides_canary() {
        let csv = sample_csv();
        let value = compute_spend_growth(&csv, &params(&csv)).unwrap();
        let encoded = serde_json::to_string(&value).unwrap();
        assert!(encoded.contains("United Kingdom"));
        assert!(encoded.contains("Germany"));
        assert!(!encoded.contains("CANARY"));
        assert!(!encoded.contains("Canaryland"));
        assert_eq!(value["results"][0]["cohort_a"], "100+");
    }

    #[test]
    fn rejects_wrong_hash() {
        let csv = sample_csv();
        let mut invalid = params(&csv);
        invalid.expected_sha256 = "00".repeat(32);
        assert!(compute_spend_growth(&csv, &invalid).is_err());
    }

    #[test]
    fn rejects_disallowed_country() {
        let csv = sample_csv();
        let mut invalid = params(&csv);
        invalid.countries = vec!["Canaryland".to_string()];
        assert!(compute_spend_growth(&csv, &invalid).is_err());
    }

    #[test]
    fn suppresses_small_cohort() {
        let csv = sample_csv();
        let mut invalid = params(&csv);
        invalid.min_cohort_size = Some(101);
        let value = compute_spend_growth(&csv, &invalid).unwrap();
        assert_eq!(value["results"][0]["spend_a"], Value::Null);
        assert_eq!(value["results"][0]["cohort_a"], "suppressed");
    }

    #[test]
    fn upload_meta_matches_hash() {
        let csv = sample_csv();
        let hash = sha256_hex(csv.as_bytes());
        let value = upload_dataset_meta("retail_v1", csv.as_bytes(), &hash).unwrap();
        assert_eq!(value["sha256"], hash);
    }
}
