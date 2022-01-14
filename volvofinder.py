import requests
import sys
from typing import Tuple
import json


def get_content_code_from_blocket_url(url: str) -> str:
    """
    https://www.blocket.se/annons/vasterbotten/volvo_v60_cross_country_d4_awd_advanced_edt/98396299
    ->
    98396299
    """
    return url.split("/")[-1]


def get_auth_code_from_url(url: str) -> str:
    resp = requests.get(url)
    assert resp.ok, resp.text
    lower_text = resp.text.lower()

    after_props = "{" + lower_text[lower_text.find('"props":{'):]
    props = after_props[: after_props.find("</script></body></html>")]

    props_dict = json.loads(props)

    return (
        props_dict["props"]["initialreduxstate"]["authentication"]["bearertoken"]
    )


MissingStr = str
BonusPropStr = str


def is_ok(url: str) -> Tuple[bool, list[MissingStr], list[BonusPropStr]]:
    auth_code = get_auth_code_from_url(url)

    content_code: str = get_content_code_from_blocket_url(url)

    resp = requests.get(
        f"https://api.blocket.se/search_bff/v1/content/{content_code}",
        headers={"Authorization": f"Bearer {auth_code}"},
    )
    assert resp.ok, resp.text

    stuff = ""
    try:
        stuff += resp.json()["data"]["body"].lower()
    except KeyError:
        pass
    try:
        stuff += str(resp.json()["data"]["attributes"][0]["items"]).lower()
    except KeyError:
        pass

    prop_status = {
        "Harman/B&W": "harman" in stuff or "bower" in stuff,
        "HUD": "hud" in stuff in "head" in stuff,
    }
    bonus_props: list[str] = []
    if "akustik" in stuff:
        bonus_props.append("akustikrutor")

    missing_props: list[str] = [
        prop_name
        for prop_name, value in prop_status.items()
        if not value
    ]
    return all(prop_status.values()), missing_props, bonus_props


try:
    urls = [sys.argv[1]]
except IndexError:
    print("Using hard-coded urls. Otherwise, usage: PROGRAM_NAME blocket_url")
    urls = [
        "https://www.blocket.se/annons/vasterbotten/volvo_v60_cross_country_d4_awd_advanced_edt/98396299", # noqa
        "https://www.blocket.se/annons/skaraborg/volvo_v60_cross_country_t5_awd_advanced_edt/98433699",  # noqa
        "https://www.blocket.se/annons/dalarna/volvo_v60_d4_inscription__vinterhjul/95188821",  # noqa
    ]

for url in urls:
    ok, missing, bonus_props = is_ok(url)

    if ok:
        print("YES" + f" BONUS: {bonus_props}" if bonus_props else "", "-", url)
    else:
        print("NO, missing", ", ".join(missing), "-", url)
