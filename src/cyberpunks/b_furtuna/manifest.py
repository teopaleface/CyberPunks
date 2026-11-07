"""Lista fișierelor publice folosite de firul B, cu sumele de control.

Descărcările stau în `data/raw/B/` (în afara git). În git intră doar această listă și scriptul
`cyberpunks.b_furtuna.download`.

EAGLE-I: Brelsford et al. (2024), Scientific Data 11:271, https://doi.org/10.1038/s41597-024-03095-5.
Setul: https://doi.org/10.6084/m9.figshare.24237376.v4 (CC BY 4.0), versiunea 4 din 25 feb. 2026, anii 2014-2025.
Ora din fișiere e UTC. Rândurile cu zero clienți afectați lipsesc (lipsa unui rând = zero sau gol de colectare).
"""

from __future__ import annotations

FIGSHARE = "https://ndownloader.figshare.com/files/"

# nume fișier -> (id figshare, octeți, md5)
EAGLEI_FILES: dict[str, tuple[int, int, str]] = {
    "DQI.csv": (42547705, 4_338, "fca42544e0c3ee4a191985d1c6c19bc4"),
    "MCC.csv": (42547708, 40_584, "7e30d47d44cae46b3342cdabf7c84b7f"),
    "coverage_history.csv": (42547714, 11_965, "33ef0c8549a95bcc1ef52b61c2463271"),
    "eaglei_outages_2014.csv": (42547717, 78_056_250, "c7bfcf4b7fd26292f8d8801a26e8c52f"),
    "eaglei_outages_2015.csv": (42547822, 598_963_737, "774d837e6a0d4f20aab5c82448538d37"),
    "eaglei_outages_2016.csv": (42547825, 619_779_314, "8e4e85e81db474a708278aabef1198ec"),
    "eaglei_outages_2017.csv": (42547828, 698_796_929, "4faaeeb3b3e8e2d13d0e9238617ce3ce"),
    "eaglei_outages_2018.csv": (42547879, 999_210_542, "726543e4a392e220108b035ba4c52e43"),
    "eaglei_outages_2019.csv": (42547885, 1_102_778_792, "0ff77af0106486eb7bdc6c5051bd916a"),
    "eaglei_outages_2020.csv": (42547894, 1_170_699_724, "3b1e76e7ff0445da2b9a2fe4819c0e88"),
    "eaglei_outages_2021.csv": (42547891, 1_141_058_232, "b5a5912be793ca22dddcc73ca2c3379d"),
    "eaglei_outages_2022.csv": (42547897, 1_187_596_176, "0cd04f23ac90ec4ec20ce3a63dcfa25a"),
    "eaglei_outages_2023.csv": (44574907, 1_199_752_423, "4ef3f9290884b4151a43333d28f67369"),
    "eaglei_outages_2024.csv": (53581661, 1_444_846_424, "13183facf56c196c061a238303c87973"),
    "eaglei_outages_2025.csv": (62164877, 1_402_347_695, "cd2feb1282a42fb048cb6885398bc1cc"),
}

EAGLEI_META = ["DQI.csv", "MCC.csv", "coverage_history.csv"]


def eaglei_year_file(year: int) -> str:
    return f"eaglei_outages_{year}.csv"
