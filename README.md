# Panchangam Calendar Generator 🌅📅

A Python tool to generate ICS calendar files with Hindu Panchangam details (Tithi, Nakshatra, Vaara) and Sandhya Kaalam timings for multiple locations.

Primary Use: **Sandhya vandanam సంధ్యావందనము**

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features ✨

- Generate ICS calendars for multiple locations
- Includes daily Panchangam details in Telugu:
        - వారము (Weekday)
        - తిథి (Lunar day)
        - నక్షత్రము (Asterism)
        - మాసము (Vedic month)
        - అయనము (Solstice)
        - సంవత్సరము (Year name)
- Supports 60-year Hindu calendar cycle (Samvatsara)
- Persistent caching system for API responses
- Configurable Ugadi date for year transition
- Multi-language support (English/Telugu)

## Requirements 📦

- Python 3.8+
- Prokerala API account (Free tier available)
- Geonames account (for timezone lookups)

## Installation 💻

1. Clone the repository:
                ```bash
                git clone https://github.com/yourusername/panchangam-calendar-generator.git
                cd panchangam-calendar-generator
                ```

2. Install dependencies:
                ```bash
                pip install -r requirements.txt
                ```

3. Set up configuration:
                ```bash
                cp secrets.example.toml secrets.toml
                ```

## Configuration 🔧

1. API Keys (Required):
                Get free API keys from:
                - Prokerala
                - Geonames

2. Add to `secrets.toml`:
                ```toml
                [api]
                YOUR_CLIENT_ID = "your_prokerala_customer_id"
                YOUR_CLIENT_SECRET = "your_prokerala_secret"
                GEONAMES_USERNAME = "your_geonames_username"
                ```

3. Cache Management:
                - Cached API responses stored in `./panchangam_cache/`
                - Delete cache files to force fresh data fetch

## Usage 🚀

### Using `sandhya_kaalam_panchangam.py`

Basic Command:
```bash
python sandhya_kaalam_panchangam.py "Mason, OH" \
                --start-date 2025-01-01 \
                --end-date 2025-01-31 \
                --ugadi-date 2025-03-30
```

Multiple Locations:
```bash
python sandhya_kaalam_panchangam.py "Mason, OH" "Hyderabad, IN" "Bengaluru, IN" \
                --start-date 2025-01-01 \
                --end-date 2025-01-31
```

Output:
- ICS files saved in root directory:
        - `Mason_OH_sandhya_kaalam_2025.ics`
        - `Hyderabad_IN_sandhya_kaalam_2025.ics`

### Using `sandhya_kaalam.py`

Basic Command:
```bash
python sandhya_kaalam.py "Mason, OH" \
                --start-date 2025-01-01 \
                --end-date 2025-01-31
```

Output:
- ICS files saved in root directory:
        - `Mason_OH_sandhya_kaalam_2025.ics`
        - `Hyderabad_IN_sandhya_kaalam_2025.ics`

## Rate Limit Management ⚠️

Free tier limits:
- Prokerala: 100 requests/day
- Geonames: 20,000 requests/day

Recommendations:
1. Process 1 location/day (≈365 requests/location/year)
2. Use caching system (persists between runs)
3. Add delays between locations:
                ```python
                # In main(), after process_location()
                time.sleep(10)  # 10-second delay between locations
                ```

## Example Output 📅

ICS Event Description:
```
ప్రాతః సంధ్యా సమయం Mason, OH వద్ద 2025-03-15న
సంవత్సరము: క్రోధి నామ సంవత్సరం
అయనము: ఉత్తరాయణము
మాసము: ఫాల్గుణ
తిథి: శుక్ల పంచమి
వారము: భాను వారము
నక్షత్రము: మృగశిర
```

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

1. శ్రీ షణ్ముఖ శర్మ గారి ప్రవచనం [https://youtu.be/fg7WPkkVD_s?si=M3fIxZsF80OsS4ok&t=4322]
2. Deepseek R1, ChatGPT 3, GitHub Copilot
3. Panchangam data powered by Prokerala API
4. Timezone data from Geonames
5. Sunrise/Sunset times from Sunrise-Sunset API

Author: Goutham Mylavarapu
Email: goutham.mylavarapu@gmail.com
Last updated: 29 January 2025