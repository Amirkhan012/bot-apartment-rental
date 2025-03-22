from typing import List, Dict, Optional

import aiohttp

from telegram.config import BOT_EMAIL


async def geocode_address(address: str) -> List[Dict[str, Optional[str]]]:
    """
    Геокодирует адрес и возвращает до 5 вариантов адресов с городами.
    """
    url = ("https://nominatim.openstreetmap.org/"
           f"search?q={address}&format=json&addressdetails=1&limit=5")
    headers = {
        "User-Agent": f"Botinok19_bot/1.0 ({BOT_EMAIL})"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            result = await response.json()
            addresses = []

            for location in result:
                addr = location.get("address", {})
                house_number = addr.get("house_number")
                road = (addr.get("road") or addr.get("pedestrian") or
                        addr.get("path"))
                city = (addr.get("city") or addr.get("town") or
                        addr.get("village"))
                region = (addr.get("county") or addr.get("state_district") or
                          addr.get("state"))

                if house_number and road and city:
                    addresses.append({
                        "house_number": house_number,
                        "road": road,
                        "region": region if region else "Не указан",
                        "city": city,
                        "display_name": location["display_name"]
                    })

            return addresses
