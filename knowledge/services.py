import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
RULES_FILE = DATASET_DIR / "rules_cleaned.jsonl"


def load_rules() -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []

    if not RULES_FILE.exists():
        return rules

    with open(RULES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rules.append(json.loads(line))

    return rules


def normalize_sensor_data(sensor_data: dict[str, Any]) -> dict[str, Any]:
    """
    Ham sensör verisini evaluator için normalize eder.
    Buradaki eşikler ilk MVP için basit tutuldu.
    """
    data = dict(sensor_data)

    # Alias desteği
    if "temp" not in data and "temperature" in data:
        data["temp"] = data["temperature"]

    if "high_humidity" not in data and "humidity" in data:
        data["high_humidity"] = data["humidity"] > 85

    if "low_humidity" not in data and "humidity" in data:
        data["low_humidity"] = data["humidity"] < 50

    if "low_light" not in data and "light" in data:
        data["low_light"] = data["light"] < 200

    if "water_deficit" not in data and "soil_moisture" in data:
        data["water_deficit"] = data["soil_moisture"] < 30

    if "over_irrigation" not in data and "soil_moisture" in data:
        data["over_irrigation"] = data["soil_moisture"] > 80

    return data


def parse_value(raw: str) -> Any:
    raw = raw.strip()

    # Fahrenheit destekli ama şu an veri Celsius ise çok kullanmayacaksın
    if raw.endswith("F"):
        return float(raw[:-1])

    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def compare(left: Any, operator: str, right: Any) -> bool:
    if left is None:
        return False

    try:
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "==":
            return left == right
    except TypeError:
        return False

    return False


def evaluate_simple_condition(condition: str, sensor_data: dict[str, Any]) -> bool:
    """
    Tek bir condition parçasını değerlendirir.
    Örnekler:
    - temperature < 14
    - humidity > 90
    - low_light
    - over_irrigation
    """
    tokens = condition.strip().split()

    # Sembolik rule: low_light, water_deficit, vb.
    if len(tokens) == 1:
        key = tokens[0]
        return bool(sensor_data.get(key, False))

    # Karşılaştırmalı rule: temperature < 14
    if len(tokens) == 3:
        field, operator, raw_value = tokens
        sensor_value = sensor_data.get(field)
        value = parse_value(raw_value)
        return compare(sensor_value, operator, value)

    return False


def evaluate_condition(condition: str, sensor_data: dict[str, Any]) -> bool:
    """
    AND / OR destekler.
    Önce OR, sonra her parçada AND kontrolü yapılır.
    Örnek:
    - ph < 6 OR ph > 6.5
    - low_light AND high_humidity
    """
    or_parts = [part.strip() for part in condition.split(" OR ")]

    for or_part in or_parts:
        and_parts = [part.strip() for part in or_part.split(" AND ")]
        if all(evaluate_simple_condition(part, sensor_data) for part in and_parts):
            return True

    return False


def evaluate_rules(sensor_data: dict[str, Any], crop: str = "domates") -> list[dict[str, Any]]:
    normalized_data = normalize_sensor_data(sensor_data)
    rules = load_rules()
    matched_rules: list[dict[str, Any]] = []

    for rule in rules:
        if rule.get("crop") != crop:
            continue

        condition = rule.get("condition", "").strip()
        if not condition:
            continue

        if evaluate_condition(condition, normalized_data):
            matched_rules.append(rule)

    return matched_rules


def generate_advice(sensor_data: dict[str, Any], crop: str = "domates") -> dict[str, Any]:
    matched = evaluate_rules(sensor_data, crop=crop)

    if not matched:
        return {
            "status": "ok",
            "message": "Şu an tanımlı kurallara göre kritik bir risk görünmüyor.",
            "matched_rules": [],
        }

    effects = [rule["effect"] for rule in matched]
    actions = [rule["action"] for rule in matched]

    return {
        "status": "warning",
        "message": "Riskli koşullar tespit edildi.",
        "matched_rules": matched,
        "effects": effects,
        "actions": actions,
    }