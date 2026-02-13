from pydantic import BaseModel, RootModel
from typing import Dict, Union

ConfigValue = Union[bool, int, float, str]
ConfigKey = str


class AdminConfigValue(BaseModel):
    """
    Single config value payload.
    """

    configValue: ConfigValue


class AdminConfigMap(RootModel[Dict[ConfigKey, ConfigValue]]):
    """
    Full admin config response shape for GET/PUT.
    """
