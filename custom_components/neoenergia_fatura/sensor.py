"""Sensores da Neoenergia Fatura (fatura + geracao solar) a partir dos PDFs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_REAL, UnitOfEnergy, UnitOfPower
from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import NeoenergiaFaturaCoordinator
    from .data import NeoenergiaFaturaConfigEntry


@dataclass(frozen=True, kw_only=True)
class NeoDesc(SensorEntityDescription):
    """Descricao com a fonte (fatura|gd) e o getter."""

    source: str
    value: Callable[[dict[str, Any]], Any]


def _g(key: str) -> Callable[[dict[str, Any]], Any]:
    return lambda d: d.get(key)


SENSORS: tuple[NeoDesc, ...] = (
    NeoDesc(
        key="valor", translation_key="valor", source="fatura",
        native_unit_of_measurement=CURRENCY_REAL,
        device_class=SensorDeviceClass.MONETARY, value=_g("valor"),
    ),
    NeoDesc(
        key="vencimento", translation_key="vencimento", source="fatura",
        device_class=SensorDeviceClass.DATE, value=_g("vencimento"),
    ),
    NeoDesc(
        key="consumo", translation_key="consumo", source="fatura",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL,
        value=_g("consumo_kwh"),
    ),
    NeoDesc(
        key="energia_injetada", translation_key="energia_injetada", source="fatura",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL,
        value=_g("energia_injetada_kwh"),
    ),
    NeoDesc(
        key="saldo_creditos", translation_key="saldo_creditos", source="fatura",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT, value=_g("saldo_creditos_kwh"),
    ),
    NeoDesc(
        key="bandeira", translation_key="bandeira", source="fatura",
        value=_g("bandeira"),
    ),
    # Geracao distribuida (demonstrativo solar)
    NeoDesc(
        key="potencia", translation_key="potencia", source="gd",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER, value=_g("potencia_kwp"),
    ),
    NeoDesc(
        key="gd_saldo_acumulado", translation_key="gd_saldo_acumulado", source="gd",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT, value=_g("saldo_acumulado_kwh"),
    ),
    NeoDesc(
        key="gd_injetada_mes", translation_key="gd_injetada_mes", source="gd",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL,
        value=_g("injetada_mes_kwh"),
    ),
    NeoDesc(
        key="gd_compensada_mes", translation_key="gd_compensada_mes", source="gd",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL,
        value=_g("compensada_mes_kwh"),
    ),
    NeoDesc(
        key="gd_total_injetado", translation_key="gd_total_injetado", source="gd",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING, value=_g("total_injetado_kwh"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NeoenergiaFaturaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Cria os sensores."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        NeoenergiaFaturaSensor(coordinator, desc, entry.entry_id) for desc in SENSORS
    )


class NeoenergiaFaturaSensor(
    CoordinatorEntity["NeoenergiaFaturaCoordinator"], SensorEntity
):
    """Sensor generico de fatura/geracao solar."""

    _attr_has_entity_name = True
    entity_description: NeoDesc

    def __init__(
        self,
        coordinator: NeoenergiaFaturaCoordinator,
        description: NeoDesc,
        entry_id: str,
    ) -> None:
        """Inicializa o sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            manufacturer="Neoenergia",
            model="Cosern (fatura por e-mail)",
            name="Cosern",
        )

    @property
    def native_value(self) -> Any:
        """Valor do sensor a partir do bloco (fatura|gd) correspondente."""
        block = (self.coordinator.data or {}).get(self.entity_description.source)
        if not block:
            return None
        return self.entity_description.value(block)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Linha digitavel/historico ficam como atributos onde fizer sentido."""
        block = (self.coordinator.data or {}).get(self.entity_description.source) or {}
        if self.entity_description.key == "valor":
            return {
                "referencia": block.get("referencia"),
                "codigo_cliente": block.get("codigo_cliente"),
                "uc": block.get("uc"),
                "linha_digitavel": block.get("linha_digitavel"),
                "nota_fiscal": block.get("nota_fiscal"),
            }
        if self.entity_description.key == "consumo":
            return {
                "leitura_anterior": block.get("leitura_anterior"),
                "leitura_atual": block.get("leitura_atual"),
                "proxima_leitura": block.get("proxima_leitura"),
                "dias_faturados": block.get("dias_faturados"),
                "historico": block.get("historico_consumo"),
            }
        return None
