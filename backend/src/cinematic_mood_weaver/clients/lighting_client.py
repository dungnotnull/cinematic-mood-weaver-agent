"""Smart lighting controller — Philips Hue and Home Assistant support.

Provides a unified interface for activating light scenes by mood.
Falls back gracefully when no smart home hub is available.
"""

from __future__ import annotations

import logging
from typing import Optional

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.types.models import LightScene

logger = logging.getLogger(__name__)


class LightingClient:
    """Unified smart lighting controller.

    Supports Philips Hue (via phue) and Home Assistant (via REST API).
    Gracefully degrades when no hub is available.
    """

    def __init__(self):
        self._hue: Optional[object] = None

    async def activate_scene(self, scene: LightScene) -> bool:
        """Activate a lighting scene. Returns True on success, False if no hub available."""
        if settings.hue_bridge_ip:
            return await self._activate_hue(scene)
        elif settings.home_assistant_url:
            return await self._activate_home_assistant(scene)
        else:
            logger.info("No smart lighting hub configured — skipping light scene activation")
            return False

    async def _activate_hue(self, scene: LightScene) -> bool:
        """Activate a scene on a Philips Hue bridge."""
        try:
            from phue import Bridge
            bridge = Bridge(settings.hue_bridge_ip)
            bridge.connect()

            # Try to find and activate a scene by name
            scene_list = bridge.get_scene()
            for group_id, scenes in scene_list.items():
                for scene_id, scene_name in scenes.items():
                    if scene_name.lower() == scene.scene_name.lower():
                        bridge.run_scene(group_id, scene_id)
                        logger.info(f"Activated Hue scene: {scene.scene_name}")
                        return True

            # Fallback: set all lights to the specified color temp and brightness
            bridge.set_light(bridge.get_light_id("all"), "on", True)
            bridge.set_light(bridge.get_light_id("all"), "bri", scene.brightness)
            bridge.set_light(bridge.get_light_id("all"), "ct", scene.color_temperature)
            bridge.set_light(bridge.get_light_id("all"), "transitiontime", scene.transition_ms // 100)
            logger.info(f"Set all Hue lights to CT={scene.color_temperature}, bri={scene.brightness}")
            return True

        except Exception as e:
            logger.warning(f"Failed to activate Hue scene: {e}")
            return False

    async def _activate_home_assistant(self, scene: LightScene) -> bool:
        """Activate a scene via Home Assistant REST API."""
        import aiohttp

        headers = {
            "Authorization": f"Bearer {settings.home_assistant_token}",
            "Content-Type": "application/json",
        }
        data = {
            "entity_id": "light.all_lights",
            "brightness": scene.brightness,
            "color_temp": scene.color_temperature,
            "transition": scene.transition_ms // 1000,
        }

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    f"{settings.home_assistant_url}/api/services/light/turn_on",
                    json=data,
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Activated Home Assistant lights: CT={scene.color_temperature}")
                        return True
                    logger.error(f"Home Assistant error: {resp.status}")
                    return False
        except Exception as e:
            logger.warning(f"Failed to activate Home Assistant: {e}")
            return False

    async def turn_off(self) -> bool:
        """Turn off all smart lights."""
        if settings.hue_bridge_ip:
            try:
                from phue import Bridge
                bridge = Bridge(settings.hue_bridge_ip)
                bridge.connect()
                bridge.set_light(bridge.get_light_id("all"), "on", False)
                return True
            except Exception:
                return False
        return False
