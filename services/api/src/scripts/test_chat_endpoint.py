import sys
import io
import os
import json
import re
import requests
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

BASE_URL      = "http://localhost:8000"
TEST_EMAIL    = "yigitemreerten@gmail.com"
TEST_PASSWORD = "Junshu(00)"
TEST_CASES_FILE = "test_cases.json"

# Sonuclar bu dosyaya kaydedilecek
REPORT_FILE = "test_report.json"


def run_tests():
    print("\n=== Developlus Chat Endpoint Testi Basliyor ===\n")

    # 1. JSON dosyasini oku
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path   = os.path.join(current_dir, TEST_CASES_FILE)
    report_path = os.path.join(current_dir, REPORT_FILE)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print(f"HATA: {TEST_CASES_FILE} bulunamadi.")
        return
    except json.JSONDecodeError:
        print(f"HATA: {TEST_CASES_FILE} gecerli bir JSON degil.")
        return

    # 2. Giris yap
    print(">> Giris yapiliyor...")
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    if login_resp.status_code != 200:
        print(f"HATA: Giris basarisiz ({login_resp.status_code}): {login_resp.text}")
        return

    access_token = login_resp.json().get("access_token")
    if not access_token:
        print("HATA: Access token alinamadi.")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    print(">> Giris basarili.\n")

    results = []
    passed_count = 0
    total_count  = len(test_cases)

    for i, test in enumerate(test_cases, 1):
        name = test["name"]
        category = name.split("]")[0].replace("[", "").strip()
        result = {
            "index":    i,
            "name":     name,
            "category": category,
            "status":   None,
            "reason":   None,
            "layers":   None,
            "llm_response_preview": None,
        }

        print(f"[{i:02d}/{total_count}] {name}")

        try:
            # Her test icin yeni, temiz bir proje olustur
            proj_resp = requests.post(
                f"{BASE_URL}/projects/",
                headers=headers,
                json={"project_name": f"Test-{i}", "description": "Otomatik test"},
            )
            if proj_resp.status_code not in (200, 201):
                msg = f"Proje olusturulamadi: {proj_resp.text}"
                print(f"  [FAIL] {msg}")
                result.update(status="FAIL", reason=msg)
                results.append(result)
                continue

            pid        = proj_resp.json().get("id")
            chat_url   = f"{BASE_URL}/projects/{pid}/chat/stream"
            survey_url = f"{BASE_URL}/projects/{pid}/survey"
            stack_url  = f"{BASE_URL}/projects/{pid}/stack"

            # Survey verisini yukle
            if "survey_data" in test:
                s = requests.put(survey_url, headers=headers, json=test["survey_data"])
                if s.status_code != 200:
                    msg = f"Survey yuklenemedi ({s.status_code})"
                    print(f"  [FAIL] {msg}")
                    result.update(status="FAIL", reason=msg)
                    results.append(result)
                    continue

            # Chat istegi gonder — SSE akisini tamamen tukenmesini bekle
            chat_resp = requests.post(
                chat_url,
                headers=headers,
                json=test["payload"],
                stream=True,
                timeout=120,
            )
            if chat_resp.status_code != 200:
                msg = f"Chat HTTP {chat_resp.status_code}"
                print(f"  [FAIL] {msg}")
                result.update(status="FAIL", reason=msg)
                results.append(result)
                continue

            full_text = ""
            for raw_line in chat_resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                try:
                    chunk = json.loads(line[6:])
                    if "token" in chunk:
                        full_text += chunk["token"]
                except json.JSONDecodeError:
                    pass

            result["llm_response_preview"] = full_text[:500]

            # Kural 1: Kod blogu yasagi
            if "```" in full_text:
                msg = "Yanit '```' (code block) iceriyor — yasak"
                print(f"  [FAIL] {msg}")
                result.update(status="FAIL", reason=msg)
                results.append(result)
                continue

            # Kural 2: Stack DB'ye kaydedildi mi? (GET /stack ile dogrula)
            stack_resp = requests.get(stack_url, headers=headers)

            if stack_resp.status_code == 404:
                if category in ("Edge Case", "Injection", "Format"):
                    msg = "Stack uretilmedi (beklenen davranis bu kategori icin)"
                    print(f"  [PASS] {msg}")
                    result.update(status="PASS", reason=msg)
                    passed_count += 1
                else:
                    msg = "Happy Path: Stack DB'ye kaydedilmedi (404)"
                    print(f"  [FAIL] {msg}")
                    result.update(status="FAIL", reason=msg)
                results.append(result)
                continue

            if stack_resp.status_code != 200:
                msg = f"/stack endpoint {stack_resp.status_code} dondu"
                print(f"  [FAIL] {msg}")
                result.update(status="FAIL", reason=msg)
                results.append(result)
                continue

            layers = stack_resp.json().get("layers")

            if not layers or not isinstance(layers, dict) or len(layers) == 0:
                msg = f"'layers' alani bos veya gecersiz: {layers}"
                print(f"  [FAIL] {msg}")
                result.update(status="FAIL", reason=msg)
                results.append(result)
                continue

            bad = {k: v for k, v in layers.items() if not isinstance(v, str)}
            if bad:
                msg = f"Bazi katman degerleri nested obj (string olmali): {list(bad.keys())}"
                print(f"  [FAIL] {msg}")
                result.update(status="FAIL", reason=msg)
                results.append(result)
                continue

            layer_names = list(layers.keys())
            msg = f"{len(layers)} dinamik katman kaydedildi -> {layer_names}"
            print(f"  [PASS] {msg}")
            result.update(status="PASS", reason=msg, layers=layers)
            passed_count += 1
            results.append(result)

        except Exception as exc:
            msg = f"Beklenmeyen hata: {exc}"
            print(f"  [FAIL] {msg}")
            result.update(status="FAIL", reason=msg)
            results.append(result)

    # ---------------------------------------------------------------------
    # Raporu JSON dosyasina kaydet
    # ---------------------------------------------------------------------
    report = {
        "run_at":       datetime.now().isoformat(),
        "total":        total_count,
        "passed":       passed_count,
        "failed":       total_count - passed_count,
        "pass_rate":    f"{passed_count / total_count * 100:.1f}%",
        "by_category":  {},
        "results":      results,
    }

    # Kategoriye gore ozet
    for r in results:
        cat = r["category"]
        report["by_category"].setdefault(cat, {"total": 0, "passed": 0})
        report["by_category"][cat]["total"] += 1
        if r["status"] == "PASS":
            report["by_category"][cat]["passed"] += 1

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------------------
    # Terminal ozeti
    # ---------------------------------------------------------------------
    print("\n" + "=" * 52)
    print(f"  OZET: {passed_count}/{total_count} BASARILI  ({report['pass_rate']})")
    print("=" * 52)
    for cat, data in report["by_category"].items():
        print(f"  {cat:<20} {data['passed']}/{data['total']}")
    print("=" * 52)
    print(f"  Detayli rapor: {report_path}")
    print("=" * 52)

    if passed_count < total_count:
        print("\n-- Basarisiz Testler --")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  [{r['index']:02d}] {r['name']}")
                print(f"       Sebep : {r['reason']}")
                if r["llm_response_preview"]:
                    preview = r["llm_response_preview"].replace("\n", " ")[:200]
                    print(f"       Yanit : {preview}")


if __name__ == "__main__":
    run_tests()
