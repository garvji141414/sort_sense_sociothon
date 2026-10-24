# SortSense — AI-Based Waste Identification & Segregation
**Sociothon 2026 · NSS IIT Roorkee** · Team: **team_name** — Arpit Seth, Rajeev Maheshwari, Garv Agarwal

> “Every item in the right bin — decided in under a second, at the point of disposal.”

## Contents
| File | Deliverable |
|---|---|
| `SortSense_Presentation.pptx` | 5 · Final presentation (official template) |
| `SortSense_Project_Report.pdf` | 2 · Solution explanation, 3 · Impact assessment, 4 · Implementation plan |
| `prototype/index.html` | 1 · Working prototype (web app, on-device AI) |
| `model/train_sortsense.py` | Custom model training + accuracy/threshold evaluation + TFLite export |
| `hardware/sortsense_bin.ino` | ESP32-CAM smart-bin station firmware |

## Run the prototype (demo)
1. Open `prototype/index.html` in Chrome/Edge (internet needed once to load TensorFlow.js + MobileNetV2).
2. Upload or capture a photo of a waste item, or type its name.
3. Confident prediction (≥ 80%) → the correct lid opens in the bin simulation and the item is logged.
   Low confidence → you confirm the bin; that answer is stored as a training label.
4. Dashboard shows items sorted, auto-sort share, category chart; export a CSV log.

Live-camera mode needs `https` or `localhost`: run `python -m http.server 8000` in `prototype/` and open `http://localhost:8000`.

## Demo script (2 min)
banana peel → Biodegradable · plastic bottle → Recyclable · type "chips packet" → Non-recyclable ·
type "AA battery" → Hazardous · a cluttered/unclear photo → human-confirm fallback · show dashboard + CSV.
